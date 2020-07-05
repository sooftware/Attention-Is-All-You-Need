"""
@github{
    title = {PyTorch Transformer},
    author = {Soohwan Kim},
    pyblisher = {GitHub},
    url = {https://github.com/sooftware/PyTorch-Transformer},
    year = {2020}
}
"""
import torch
import torch.nn as nn


class Transformer(nn.Module):
    """
    A Transformer model. User is able to modify the attributes as needed.
    The architecture is based on the paper "Attention Is All You Need".
    https://arxiv.org/abs/1706.03762

    Args: d_model, num_heads, num_layers, num_classes

    """
    def __init__(self, num_classes: int, d_model: int = 512,
                 num_encoder_layers: int = 6, num_decoder_layers: int = 6,
                 num_heads: int = 8, dropout_p: float = 0.3):
        super(Transformer, self).__init__()
        self.encoder = TransformerEncoder(d_model, num_encoder_layers, num_heads, dropout_p)
        self.decoder = TransformerDecoder(d_model, num_decoder_layers, num_heads, dropout_p)
        self.linear_out = nn.Linear(d_model, num_classes)

    def forward(self, encoder_inputs: torch.Tensor, decoder_inputs: torch.Tensor):
        encoder_outputs = self.encoder(encoder_inputs)
        decoder_outputs = self.decoder(decoder_inputs, encoder_outputs)
        result = self.linear_out(decoder_outputs)
        return result


class TransformerEncoder(nn.Module):
    """
    Encoder of Transformer: stack of N encoder layers
    """
    def __init__(self, d_model: int = 512, num_layers: int = 6, num_heads: int = 8, dropout_p: float = 0.3):
        super(TransformerEncoder, self).__init__()
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads

    def forward(self):
        pass


class TransformerDecoder(nn.Module):
    """ Decoder of Transformer:  stack of N decoder layers """
    def __init__(self, d_model: int = 512, num_layers: int = 6, num_heads: int = 8, dropout_p: float = 0.3):
        super(TransformerDecoder, self).__init__()
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads

    def forward(self):
        pass


class PositionalEncoding(nn.Module):
    def __init__(self):
        super(PositionalEncoding, self).__init__()

    def forward(self):
        pass