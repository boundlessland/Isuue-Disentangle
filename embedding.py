#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/13 21:00
# @Author  : jsx
# @File    : embedding.py
# @Description :
import fasttext
import numpy as np
import torch
from transformers import BertModel, BertTokenizer

import config


class TextEncoder:
    def __init__(self, encoder):
        self.name = encoder
        if encoder == 'bert':
            self.model = BertModel.from_pretrained('bert-base-uncased')
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            self.model.eval()
        elif encoder == 'fasttext':
            self.model = fasttext.load_model(config.ModelPath.FASTTEXTMODELEN300D)

    def getSentenceVector(self, wordLst):
        wordsVecLst = []
        sentenceVec = []
        if len(wordLst) == 0:
            return sentenceVec
        if self.name == 'fasttext':
            for w in wordLst:
                wordVec = self.model.get_word_vector(w).tolist()
                wordsVecLst.append(wordVec)
            sentenceVec = np.mean(np.array(wordsVecLst), 0).tolist()
            # print(sentenceVec)
        elif self.name == 'bert':
            indexedTokens = self.tokenizer.convert_tokens_to_ids(wordLst)  # 得到每个词在词表中的索引
            segmentsIDs = [1] * len(wordLst)
            tokensTensor = torch.tensor([indexedTokens])
            segmentsTensors = torch.tensor([segmentsIDs])
            with torch.no_grad():
                outputs = self.model(tokensTensor, segmentsTensors)
                hidden_states = outputs[2]
            tokenEmbeddings = torch.stack(hidden_states, dim=0)
            tokenEmbeddings.size()
            tokenEmbeddings = torch.squeeze(tokenEmbeddings, dim=1)
            tokenEmbeddings.size()
            tokenEmbeddings = tokenEmbeddings.permute(1, 0, 2)  # 调换顺序
            tokenEmbeddings.size()
            # 词向量表示
            tokenVecsCat = [torch.cat((layer[-1], layer[-2], layer[-3], layer[-4]), 0) for layer in
                            tokenEmbeddings]  # 连接最后四层 [number_of_tokens, 3072]
            wordsVecLst = [torch.sum(layer[-4:], 0) for layer in tokenEmbeddings]  # 对最后四层求和 [number_of_tokens, 768]

            # 句子向量表示
            tokenVecs = hidden_states[-2][0]
            sentenceVec = torch.mean(tokenVecs, dim=0)  # 一个句子就是768维度
        return sentenceVec
