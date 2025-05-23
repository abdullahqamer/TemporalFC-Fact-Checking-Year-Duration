"""Euclidean Knowledge Graph embedding models where embeddings are in complex space."""
import torch
from torch import nn
import numpy as np

from models.base import KGModel
from utils.euclidean import givens_complex_product

STWO_MODELS = ["sTwoComplEx"]


class BaseC(KGModel):
    """Complex Knowledge Graph Embedding models.

    Attributes:
        embeddings: complex embeddings for entities and relations
    """

    def __init__(self, args):
        """Initialize a Complex KGModel."""
        super(BaseC, self).__init__(args.sizes, args.rank, args.dropout, args.gamma, args.dtype, args.bias,
                                    args.init_size, args)
        assert self.rank % 2 == 0, "Complex models require even embedding dimension"
        #self.sizes = list(set(self.sizes))
        self.sizes = np.array(list(self.sizes))#np.expand_dims(np.array(list(self.sizes)), axis = 1)
        self.sizes = list(np.delete(self.sizes, 2, 0))
        self.rank = self.rank//2
        self.embeddings = nn.ModuleList([
            nn.Embedding(s, 2*self.rank, sparse=True)
            for s in self.sizes
        ])
        
        self.embeddings[0].weight.data = self.init_size * self.embeddings[0].weight.to(self.data_type)
        self.embeddings[1].weight.data = self.init_size * self.embeddings[1].weight.to(self.data_type)

        if len(self.sizes) == 4:                        
            self.embeddings[2].weight.data = self.init_size * self.embeddings[2].weight.to(self.data_type)
            self.embeddings[3].weight.data = self.init_size * self.embeddings[3].weight.to(self.data_type)

    def get_rhs(self, queries, eval_mode):
        """Get embeddings and biases of target entities."""
        if eval_mode:
            return self.embeddings[0].weight, self.bt.weight
        else:
            return self.embeddings[0](queries[:, 2]), self.bt(queries[:, 2])

    def similarity_score(self, lhs_e, rhs_e, eval_mode):
        """Compute similarity scores or queries against targets in embedding space."""                
      

        rhs_e = rhs_e[:, :self.rank], rhs_e[:, self.rank:2*self.rank]
        A,B = givens_complex_product(rhs_e, lhs_e, eval_mode)
        if eval_mode:
            #print(A.size()) 
            #print(B.size())
            #exit()
            return A + B
        else:
            #print(A.size())
            #print(B.size())
            #exit()
            return torch.sum(
                A + B,
                1, keepdim=True
            )

    def get_factors(self, queries):
    #    """Compute factors for embeddings' regularization."""
    #    head_e, rel_e, rhs_e = self.get_complex_embeddings(queries)
    #    head_f = torch.sqrt(head_e[0] ** 2 + head_e[1] ** 2)
    #    rel_f = torch.sqrt(rel_e[0] ** 2 + rel_e[1] ** 2)
    #    rhs_f = torch.sqrt(rhs_e[0] ** 2 + rhs_e[1] ** 2)
    #    return head_f, rel_f, rhs_f

        head_e = self.entity(queries[:, 0])
        rel_e = self.rel(queries[:, 1])
        rhs_e = self.entity(queries[:, 2])
        #loc_e = self.entity(queries[:, 3])
        #tim_e = self.entity(queries[:, 4])
        return head_e, rel_e, rhs_e

class sTwoComplEx(BaseC):
    """Euclidean translations https://www.utc.fr/~bordesan/dokuwiki/_media/en/transe_nips13.pdf"""

    def __init__(self, args):
        super(sTwoComplEx, self).__init__(args)
                      
        #self.loc_emb = nn.Embedding(self.sizes[2], self.rank)
        #self.loc_emb.weight.data = 2 * torch.rand((self.sizes[2], self.rank), dtype=self.data_type) - 1.0

        #self.tim_emb = nn.Embedding(self.sizes[3], self.rank)
        #self.tim_emb.weight.data = 2 * torch.rand((self.sizes[3], self.rank), dtype=self.data_type) - 1.0
        
        #self.rel_complement = nn.Embedding(self.sizes[1], 3*self.rank)
        #self.rel_complement.weight.data = 2 * torch.rand((self.sizes[1], 3*self.rank), dtype=self.data_type) - 1.0
        #Ended

    def get_queries(self, queries):
        head_e = self.entity(queries[:, 0])
        rel_e = self.rel(queries[:, 1])
        #rel_e_c = self.rel_complement(queries[:, 1])

        #Added
        #loc_e = self.loc_emb(queries[:, 3])
        #tim_e = self.tim_emb(queries[:, 4])
        #Ended       
        rank = self.rank
        head_e_s = head_e[:, :rank]#, head_e[:, rank//2:rank], head_e[:, rank:3*rank//2], head_e[:, 3*rank//2:]
        #rel_e_c = rel_e, rel_e_c[:, :rank], rel_e_c[:, rank:2*rank], rel_e_c[:, 2*rank:]        
        rel_e_s = rel_e[:, :rank]#, loc_rot_e[:, rank//2:rank], tim_rot_e[:, :rank//2], tim_rot_e[:, rank//2:rank]
        #loc_e_s = loc_e[:, :rank]
        #tim_e_s = tim_e[:, :rank]
        
        lhs_e = head_e_s, rel_e_s

        #ABCD = givens_incomplete_DE_mult(rel_e_c, hlt)

        #E = torch.cat((A, B), 1)
        #F = torch.cat((E, C), 1)
        #h_e = torch.cat((F, D), 1)

        #lhs_e = h_e + rel_e + loc_e + tim_e
        #lhs_e = ABCD, rel_e_c
        lhs_biases = self.bh(queries[:, 0])
        return lhs_e, lhs_biases

