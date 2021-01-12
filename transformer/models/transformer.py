"""
Author:
    - **Soohwan Kim @sooftware**
    - **Email: sh951011@gmail.com**

Reference :
    - **https://github.com/graykode/nlp-tutorial**
    - **https://github.com/dreamgonfly/transformer-pytorch**
    - **https://github.com/jadore801120/attention-is-all-you-need-pytorch**
    - **https://github.com/JayParks/transformer**
"""
import torch.nn as nn
from torch import Tensor
from typing import Optional, Tuple
from transformer.models.modules import Linear
from transformer.models.mask import subsequent_masking, pad_masking, get_pad_mask, get_attn_pad_mask, \
    get_subsequent_mask
from transformer.models.embeddings import Embedding, PositionalEncoding
from transformer.models.layers import TransformerEncoderLayer, TransformerDecoderLayer


class Transformer(nn.Module):
    """
    A Transformer model. User is able to modify the attributes as needed.
    The architecture is based on the paper "Attention Is All You Need".

    Args:
        num_classes (int): the number of classfication
        pad_id (int): identification of <PAD_token>
        num_input_embeddings (int): dimension of input embeddings
        num_output_embeddings (int): dimenstion of output embeddings
        d_model (int): dimension of model (default: 512)
        d_ff (int): dimension of feed forward network (default: 2048)
        num_encoder_layers (int): number of encoder layers (default: 6)
        num_decoder_layers (int): number of decoder layers (default: 6)
        num_heads (int): number of attention heads (default: 8)
        dropout_p (float): dropout probability (default: 0.3)
        ffnet_style (str): if poswise_ffnet is 'ff', position-wise feed forware network to be a feed forward,
            otherwise, position-wise feed forward network to be a convolution layer. (default: ff)

    Inputs: inputs, targets
        - **inputs** (batch, input_length): tensor containing input sequences
        - **targets** (batch, target_length): tensor contatining target sequences

    Returns: output
        - **output**: tensor containing the outputs
    """
    def __init__(self, num_classes: int, pad_id: int, num_input_embeddings: int, num_output_embeddings: int,
                 d_model: int = 512, d_ff: int = 2048, num_heads: int = 8,
                 num_encoder_layers: int = 6, num_decoder_layers: int = 6,
                 dropout_p: float = 0.3, ffnet_style: str = 'ff') -> None:
        super(Transformer, self).__init__()
        self.pad_id = pad_id
        self.encoder = TransformerEncoder(num_input_embeddings, d_model, d_ff, num_encoder_layers,
                                          num_heads, ffnet_style, dropout_p, pad_id)
        self.decoder = TransformerDecoder(num_output_embeddings, d_model, d_ff, num_decoder_layers,
                                          num_heads, ffnet_style, dropout_p, pad_id)
        self.generator = Linear(d_model, num_classes)

    def forward(self, inputs: Tensor, input_lengths: Tensor,
                targets: Optional[Tensor],
                return_attns: bool = False) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        batch_size = targets.size(0)
        targets = targets[targets != self.eos_id].view(batch_size, -1)

        memory, encoder_self_attns = self.encoder(inputs, input_lengths)
        output, decoder_self_attns, memory_attns = self.decoder(targets, input_lengths, memory)
        output = self.generator(output)

        if return_attns:
            return output, encoder_self_attns, decoder_self_attns, memory_attns

        return output


class TransformerEncoder(nn.Module):
    """
    The TransformerEncoder is composed of a stack of N identical layers.
    Each layer has two sub-layers. The first is a multi-head self-attention mechanism,
    and the second is a simple, position-wise fully connected feed-forward network.
    """
    def __init__(self, num_embeddings: int, d_model: int = 512, d_ff: int = 2048,
                 num_layers: int = 6, num_heads: int = 8, ffnet_style: str = 'ff',
                 dropout_p: float = 0.3, pad_id: int = 0) -> None:
        super(TransformerEncoder, self).__init__()
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.pad_id = pad_id
        self.embedding = Embedding(num_embeddings, pad_id, d_model)
        self.pos_encoding = PositionalEncoding(d_model, dropout_p)
        self.input_dropout = nn.Dropout(p=dropout_p)
        self.layers = nn.ModuleList(
            [TransformerEncoderLayer(d_model, num_heads, d_ff, dropout_p, ffnet_style) for _ in range(num_layers)]
        )
        self.logit_scale = (d_model ** -0.5)

    def forward(self, inputs: Tensor, input_lengths: Tensor = None) -> Tuple[Tensor, Tensor]:
        self_attns = list()

        output = self.input_dropout(self.embedding(inputs) * self.logit_scale + self.pos_encoding(inputs))
        length = inputs.size(1)
        self_attn_mask = get_pad_mask(inputs, input_lengths).squeeze(-1).unsqueeze(1).expand(-1, length, -1)

        for layer in self.layers:
            output, attn = layer(output, self_attn_mask)
            self_attns.append(attn)

        return output, self_attns


class TransformerDecoder(nn.Module):
    """
    The TransformerDecoder is composed of a stack of N identical layers.
    Each layer has three sub-layers. The first is a multi-head self-attention mechanism,
    and the second is a multi-head attention mechanism, third is a feed-forward network.
    """
    def __init__(self, num_embeddings: int, d_model: int = 512, d_ff: int = 512,
                 num_layers: int = 6, num_heads: int = 8, ffnet_style: str = 'ff',
                 dropout_p: float = 0.3, pad_id: int = 0) -> None:
        super(TransformerDecoder, self).__init__()
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.embedding = Embedding(num_embeddings, pad_id, d_model)
        self.pos_encoding = PositionalEncoding(d_model, dropout_p)
        self.input_dropout = nn.Dropout(p=dropout_p)
        self.layers = nn.ModuleList(
            [TransformerDecoderLayer(d_model, num_heads, d_ff,  dropout_p, ffnet_style) for _ in range(num_layers)]
        )
        self.logit_scale = (d_model ** -0.5)

    def forward(self, targets: Tensor,
                input_lengths: Optional[Tensor] = None,
                memory: Tensor = None) -> Tuple[Tensor, Tensor, Tensor]:
        self_attns, memory_attns = list(), list()

        self_attn_mask = get_attn_pad_mask(targets, self.pad_id) | get_subsequent_mask(targets)
        memory_mask = get_pad_mask(memory, input_lengths).squeeze(-1).unsqueeze(1).expand(-1, targets.size(1), -1)

        output = self.input_dropout(self.embedding(targets) * self.logit_scale + self.pos_encoding(targets.size(1)))

        for layer in self.layers:
            output, self_attn, memory_attn = layer(output, memory, self_attn_mask, memory_mask)
            self_attns.append(self_attn)
            memory_attns.append(memory_attn)

        return output, self_attns, memory_attns
