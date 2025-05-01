import re
import difflib
import numpy as np
import re
import difflib
import numpy as np
import copy
from typing import Optional, Union, List, Dict, Any
from PIL import Image
from diffusers import StableDiffusionXLImg2ImgPipeline
import torch
from contextlib import contextmanager
from tqdm.auto import trange
from diffusers.pipelines.stable_diffusion_xl.pipeline_stable_diffusion_xl_img2img import (
    StableDiffusionXLImg2ImgPipeline,
    randn_tensor,
    StableDiffusionXLPipelineOutput,
)
from diffusers.models.transformers import Transformer2DModel
from diffusers import StableDiffusionXLImg2ImgPipeline


system_prompt = r'''You are a helpful AI assistant to compose images using the below python class `Canvas`:

```python
class Canvas:
    def set_global_description(self, description: str, detailed_descriptions: list[str], tags: str, HTML_web_color_name: str):
        pass

    def add_local_description(self, location: str, offset: str, area: str, distance_to_viewer: float, description: str, detailed_descriptions: list[str], tags: str, atmosphere: str, style: str, quality_meta: str, HTML_web_color_name: str):
        assert location in ["in the center", "on the left", "on the right", "on the top", "on the bottom", "on the top-left", "on the top-right", "on the bottom-left", "on the bottom-right"]
        assert offset in ["no offset", "slightly to the left", "slightly to the right", "slightly to the upper", "slightly to the lower", "slightly to the upper-left", "slightly to the upper-right", "slightly to the lower-left", "slightly to the lower-right"]
        assert area in ["a small square area", "a small vertical area", "a small horizontal area", "a medium-sized square area", "a medium-sized vertical area", "a medium-sized horizontal area", "a large square area", "a large vertical area", "a large horizontal area"]
        assert distance_to_viewer > 0
        pass
```'''

valid_colors = {  # r, g, b
    'aliceblue': (240, 248, 255), 'antiquewhite': (250, 235, 215), 'aqua': (0, 255, 255),
    'aquamarine': (127, 255, 212), 'azure': (240, 255, 255), 'beige': (245, 245, 220),
    'bisque': (255, 228, 196), 'black': (0, 0, 0), 'blanchedalmond': (255, 235, 205), 'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226), 'brown': (165, 42, 42), 'burlywood': (222, 184, 135),
    'cadetblue': (95, 158, 160), 'chartreuse': (127, 255, 0), 'chocolate': (210, 105, 30),
    'coral': (255, 127, 80), 'cornflowerblue': (100, 149, 237), 'cornsilk': (255, 248, 220),
    'crimson': (220, 20, 60), 'cyan': (0, 255, 255), 'darkblue': (0, 0, 139), 'darkcyan': (0, 139, 139),
    'darkgoldenrod': (184, 134, 11), 'darkgray': (169, 169, 169), 'darkgrey': (169, 169, 169),
    'darkgreen': (0, 100, 0), 'darkkhaki': (189, 183, 107), 'darkmagenta': (139, 0, 139),
    'darkolivegreen': (85, 107, 47), 'darkorange': (255, 140, 0), 'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0), 'darksalmon': (233, 150, 122), 'darkseagreen': (143, 188, 143),
    'darkslateblue': (72, 61, 139), 'darkslategray': (47, 79, 79), 'darkslategrey': (47, 79, 79),
    'darkturquoise': (0, 206, 209), 'darkviolet': (148, 0, 211), 'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255), 'dimgray': (105, 105, 105), 'dimgrey': (105, 105, 105),
    'dodgerblue': (30, 144, 255), 'firebrick': (178, 34, 34), 'floralwhite': (255, 250, 240),
    'forestgreen': (34, 139, 34), 'fuchsia': (255, 0, 255), 'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255), 'gold': (255, 215, 0), 'goldenrod': (218, 165, 32),
    'gray': (128, 128, 128), 'grey': (128, 128, 128), 'green': (0, 128, 0), 'greenyellow': (173, 255, 47),
    'honeydew': (240, 255, 240), 'hotpink': (255, 105, 180), 'indianred': (205, 92, 92),
    'indigo': (75, 0, 130), 'ivory': (255, 255, 240), 'khaki': (240, 230, 140), 'lavender': (230, 230, 250),
    'lavenderblush': (255, 240, 245), 'lawngreen': (124, 252, 0), 'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230), 'lightcoral': (240, 128, 128), 'lightcyan': (224, 255, 255),
    'lightgoldenrodyellow': (250, 250, 210), 'lightgray': (211, 211, 211), 'lightgrey': (211, 211, 211),
    'lightgreen': (144, 238, 144), 'lightpink': (255, 182, 193), 'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170), 'lightskyblue': (135, 206, 250), 'lightslategray': (119, 136, 153),
    'lightslategrey': (119, 136, 153), 'lightsteelblue': (176, 196, 222), 'lightyellow': (255, 255, 224),
    'lime': (0, 255, 0), 'limegreen': (50, 205, 50), 'linen': (250, 240, 230), 'magenta': (255, 0, 255),
    'maroon': (128, 0, 0), 'mediumaquamarine': (102, 205, 170), 'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211), 'mediumpurple': (147, 112, 219), 'mediumseagreen': (60, 179, 113),
    'mediumslateblue': (123, 104, 238), 'mediumspringgreen': (0, 250, 154),
    'mediumturquoise': (72, 209, 204), 'mediumvioletred': (199, 21, 133), 'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250), 'mistyrose': (255, 228, 225), 'moccasin': (255, 228, 181),
    'navajowhite': (255, 222, 173), 'navy': (0, 0, 128), 'navyblue': (0, 0, 128),
    'oldlace': (253, 245, 230), 'olive': (128, 128, 0), 'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0), 'orangered': (255, 69, 0), 'orchid': (218, 112, 214),
    'palegoldenrod': (238, 232, 170), 'palegreen': (152, 251, 152), 'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147), 'papayawhip': (255, 239, 213), 'peachpuff': (255, 218, 185),
    'peru': (205, 133, 63), 'pink': (255, 192, 203), 'plum': (221, 160, 221), 'powderblue': (176, 224, 230),
    'purple': (128, 0, 128), 'rebeccapurple': (102, 51, 153), 'red': (255, 0, 0),
    'rosybrown': (188, 143, 143), 'royalblue': (65, 105, 225), 'saddlebrown': (139, 69, 19),
    'salmon': (250, 128, 114), 'sandybrown': (244, 164, 96), 'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238), 'sienna': (160, 82, 45), 'silver': (192, 192, 192),
    'skyblue': (135, 206, 235), 'slateblue': (106, 90, 205), 'slategray': (112, 128, 144),
    'slategrey': (112, 128, 144), 'snow': (255, 250, 250), 'springgreen': (0, 255, 127),
    'steelblue': (70, 130, 180), 'tan': (210, 180, 140), 'teal': (0, 128, 128), 'thistle': (216, 191, 216),
    'tomato': (255, 99, 71), 'turquoise': (64, 224, 208), 'violet': (238, 130, 238),
    'wheat': (245, 222, 179), 'white': (255, 255, 255), 'whitesmoke': (245, 245, 245),
    'yellow': (255, 255, 0), 'yellowgreen': (154, 205, 50)
}

valid_locations = {  # x, y in 90*90
    'in the center': (45, 45),
    'on the left': (15, 45),
    'on the right': (75, 45),
    'on the top': (45, 15),
    'on the bottom': (45, 75),
    'on the top-left': (15, 15),
    'on the top-right': (75, 15),
    'on the bottom-left': (15, 75),
    'on the bottom-right': (75, 75)
}

valid_offsets = {  # x, y in 90*90
    'no offset': (0, 0),
    'slightly to the left': (-10, 0),
    'slightly to the right': (10, 0),
    'slightly to the upper': (0, -10),
    'slightly to the lower': (0, 10),
    'slightly to the upper-left': (-10, -10),
    'slightly to the upper-right': (10, -10),
    'slightly to the lower-left': (-10, 10),
    'slightly to the lower-right': (10, 10)}

valid_areas = {  # w, h in 90*90
    "a small square area": (50, 50),
    "a small vertical area": (40, 60),
    "a small horizontal area": (60, 40),
    "a medium-sized square area": (60, 60),
    "a medium-sized vertical area": (50, 80),
    "a medium-sized horizontal area": (80, 50),
    "a large square area": (70, 70),
    "a large vertical area": (60, 90),
    "a large horizontal area": (90, 60)
}


def closest_name(input_str, options):
    input_str = input_str.lower()

    closest_match = difflib.get_close_matches(input_str, list(options.keys()), n=1, cutoff=0.5)
    assert isinstance(closest_match, list) and len(closest_match) > 0, f'The value [{input_str}] is not valid!'
    result = closest_match[0]

    if result != input_str:
        print(f'Automatically corrected [{input_str}] -> [{result}].')

    return result


def safe_str(x):
    return x.strip(',. ') + '.'


def binary_nonzero_positions(n, offset=0):
    binary_str = bin(n)[2:]
    positions = [i + offset for i, bit in enumerate(reversed(binary_str)) if bit == '1']
    return positions


class Canvas:
    @staticmethod
    def from_bot_response(response: str):
        matched = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        assert matched, 'Response does not contain codes!'
        code_content = matched.group(1)
        assert 'canvas = Canvas()' in code_content, 'Code block must include valid canvas var!'
        local_vars = {'Canvas': Canvas}
        exec(code_content, {}, local_vars)
        canvas = local_vars.get('canvas', None)
        assert isinstance(canvas, Canvas), 'Code block must produce valid canvas var!'
        return canvas

    def __init__(self):
        self.components = []
        self.color = None
        self.record_tags = True
        self.prefixes = []
        self.suffixes = []
        return

    def set_global_description(self, description: str, detailed_descriptions: list[str], tags: str,
                               HTML_web_color_name: str):
        assert isinstance(description, str), 'Global description is not valid!'
        assert isinstance(detailed_descriptions, list) and all(isinstance(item, str) for item in detailed_descriptions), \
            'Global detailed_descriptions is not valid!'
        assert isinstance(tags, str), 'Global tags is not valid!'

        HTML_web_color_name = closest_name(HTML_web_color_name, valid_colors)
        self.color = np.array([[valid_colors[HTML_web_color_name]]], dtype=np.uint8)

        self.prefixes = [description]
        self.suffixes = detailed_descriptions

        if self.record_tags:
            self.suffixes = self.suffixes + [tags]

        self.prefixes = [safe_str(x) for x in self.prefixes]
        self.suffixes = [safe_str(x) for x in self.suffixes]

        return

    def add_local_description(self, location: str, offset: str, area: str, distance_to_viewer: float, description: str,
                              detailed_descriptions: list[str], tags: str, atmosphere: str, style: str,
                              quality_meta: str, HTML_web_color_name: str):
        assert isinstance(description, str), 'Local description is wrong!'
        assert isinstance(distance_to_viewer, (int, float)) and distance_to_viewer > 0, \
            f'The distance_to_viewer for [{description}] is not positive float number!'
        assert isinstance(detailed_descriptions, list) and all(isinstance(item, str) for item in detailed_descriptions), \
            f'The detailed_descriptions for [{description}] is not valid!'
        assert isinstance(tags, str), f'The tags for [{description}] is not valid!'
        assert isinstance(atmosphere, str), f'The atmosphere for [{description}] is not valid!'
        assert isinstance(style, str), f'The style for [{description}] is not valid!'
        assert isinstance(quality_meta, str), f'The quality_meta for [{description}] is not valid!'

        location = closest_name(location, valid_locations)
        offset = closest_name(offset, valid_offsets)
        area = closest_name(area, valid_areas)
        HTML_web_color_name = closest_name(HTML_web_color_name, valid_colors)

        xb, yb = valid_locations[location]
        xo, yo = valid_offsets[offset]
        w, h = valid_areas[area]
        rect = (yb + yo - h // 2, yb + yo + h // 2, xb + xo - w // 2, xb + xo + w // 2)
        rect = [max(0, min(90, i)) for i in rect]
        color = np.array([[valid_colors[HTML_web_color_name]]], dtype=np.uint8)

        prefixes = self.prefixes + [description]
        suffixes = detailed_descriptions

        if self.record_tags:
            suffixes = suffixes + [tags, atmosphere, style, quality_meta]

        prefixes = [safe_str(x) for x in prefixes]
        suffixes = [safe_str(x) for x in suffixes]

        self.components.append(dict(
            rect=rect,
            distance_to_viewer=distance_to_viewer,
            color=color,
            prefixes=prefixes,
            suffixes=suffixes
        ))

        return

    def process(self):
        # sort components
        self.components = sorted(self.components, key=lambda x: x['distance_to_viewer'], reverse=True)

        # compute initial latent
        initial_latent = np.zeros(shape=(90, 90, 3), dtype=np.float32) + self.color

        for component in self.components:
            a, b, c, d = component['rect']
            initial_latent[a:b, c:d] = 0.7 * component['color'] + 0.3 * initial_latent[a:b, c:d]

        initial_latent = initial_latent.clip(0, 255).astype(np.uint8)

        # compute conditions

        bag_of_conditions = [
            dict(mask=np.ones(shape=(90, 90), dtype=np.float32), prefixes=self.prefixes, suffixes=self.suffixes)
        ]

        for i, component in enumerate(self.components):
            a, b, c, d = component['rect']
            m = np.zeros(shape=(90, 90), dtype=np.float32)
            m[a:b, c:d] = 1.0
            bag_of_conditions.append(dict(
                mask=m,
                prefixes=component['prefixes'],
                suffixes=component['suffixes']
            ))

        return dict(
            initial_latent=initial_latent,
            bag_of_conditions=bag_of_conditions,
        )
    
import torch
from contextlib import contextmanager


high_vram = False
gpu = torch.device('cuda')
cpu = torch.device('cpu')

torch.zeros((1, 1)).to(gpu, torch.float32)
torch.cuda.empty_cache()

models_in_gpu = []


@contextmanager
def movable_bnb_model(m):
    if hasattr(m, 'quantization_method'):
        m.quantization_method_backup = m.quantization_method
        del m.quantization_method
    try:
        yield None
    finally:
        if hasattr(m, 'quantization_method_backup'):
            m.quantization_method = m.quantization_method_backup
            del m.quantization_method_backup
    return


def load_models_to_gpu(models):
    global models_in_gpu

    if not isinstance(models, (tuple, list)):
        models = [models]

    models_to_remain = [m for m in set(models) if m in models_in_gpu]
    models_to_load = [m for m in set(models) if m not in models_in_gpu]
    models_to_unload = [m for m in set(models_in_gpu) if m not in models_to_remain]

    if not high_vram:
        for m in models_to_unload:
            with movable_bnb_model(m):
                m.to(cpu)
            print('Unload to CPU:', m.__class__.__name__)
        models_in_gpu = models_to_remain

    for m in models_to_load:
        with movable_bnb_model(m):
            m.to(gpu)
        print('Load to GPU:', m.__class__.__name__)

    models_in_gpu = list(set(models_in_gpu + models))
    torch.cuda.empty_cache()
    return


def unload_all_models(extra_models=None):
    global models_in_gpu

    if extra_models is None:
        extra_models = []

    if not isinstance(extra_models, (tuple, list)):
        extra_models = [extra_models]

    models_in_gpu = list(set(models_in_gpu + extra_models))

    return load_models_to_gpu([])

import numpy as np
import copy

from tqdm.auto import trange
from diffusers.pipelines.stable_diffusion_xl.pipeline_stable_diffusion_xl_img2img import *
from diffusers.models.transformers import Transformer2DModel


original_Transformer2DModel_forward = Transformer2DModel.forward


def hacked_Transformer2DModel_forward(
        self,
        hidden_states: torch.Tensor,
        encoder_hidden_states: Optional[torch.Tensor] = None,
        timestep: Optional[torch.LongTensor] = None,
        added_cond_kwargs: Dict[str, torch.Tensor] = None,
        class_labels: Optional[torch.LongTensor] = None,
        cross_attention_kwargs: Dict[str, Any] = None,
        attention_mask: Optional[torch.Tensor] = None,
        encoder_attention_mask: Optional[torch.Tensor] = None,
        return_dict: bool = True,
):
    cross_attention_kwargs = cross_attention_kwargs or {}
    cross_attention_kwargs['hidden_states_original_shape'] = hidden_states.shape
    return original_Transformer2DModel_forward(
        self, hidden_states, encoder_hidden_states, timestep, added_cond_kwargs, class_labels, cross_attention_kwargs,
        attention_mask, encoder_attention_mask, return_dict)


Transformer2DModel.forward = hacked_Transformer2DModel_forward


@torch.no_grad()
def sample_dpmpp_2m(model, x, sigmas, extra_args=None, callback=None, disable=None):
    """DPM-Solver++(2M)."""
    extra_args = {} if extra_args is None else extra_args
    s_in = x.new_ones([x.shape[0]])
    sigma_fn = lambda t: t.neg().exp()
    t_fn = lambda sigma: sigma.log().neg()
    old_denoised = None

    for i in trange(len(sigmas) - 1, disable=disable):
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        if callback is not None:
            callback({'x': x, 'i': i, 'sigma': sigmas[i], 'sigma_hat': sigmas[i], 'denoised': denoised})
        t, t_next = t_fn(sigmas[i]), t_fn(sigmas[i + 1])
        h = t_next - t
        if old_denoised is None or sigmas[i + 1] == 0:
            x = (sigma_fn(t_next) / sigma_fn(t)) * x - (-h).expm1() * denoised
        else:
            h_last = t - t_fn(sigmas[i - 1])
            r = h_last / h
            denoised_d = (1 + 1 / (2 * r)) * denoised - (1 / (2 * r)) * old_denoised
            x = (sigma_fn(t_next) / sigma_fn(t)) * x - (-h).expm1() * denoised_d
        old_denoised = denoised
    return x


class KModel:
    def __init__(self, unet, timesteps=1000, linear_start=0.00085, linear_end=0.012):
        betas = torch.linspace(linear_start ** 0.5, linear_end ** 0.5, timesteps, dtype=torch.float64) ** 2
        alphas = 1. - betas
        alphas_cumprod = torch.tensor(np.cumprod(alphas, axis=0), dtype=torch.float32)

        self.sigmas = ((1 - alphas_cumprod) / alphas_cumprod) ** 0.5
        self.log_sigmas = self.sigmas.log()
        self.sigma_data = 1.0
        self.unet = unet
        return

    @property
    def sigma_min(self):
        return self.sigmas[0]

    @property
    def sigma_max(self):
        return self.sigmas[-1]

    def timestep(self, sigma):
        log_sigma = sigma.log()
        dists = log_sigma.to(self.log_sigmas.device) - self.log_sigmas[:, None]
        return dists.abs().argmin(dim=0).view(sigma.shape).to(sigma.device)

    def get_sigmas_karras(self, n, rho=7.):
        ramp = torch.linspace(0, 1, n)
        min_inv_rho = self.sigma_min ** (1 / rho)
        max_inv_rho = self.sigma_max ** (1 / rho)
        sigmas = (max_inv_rho + ramp * (min_inv_rho - max_inv_rho)) ** rho
        return torch.cat([sigmas, sigmas.new_zeros([1])])

    def __call__(self, x, sigma, **extra_args):
        x_ddim_space = x / (sigma[:, None, None, None] ** 2 + self.sigma_data ** 2) ** 0.5
        t = self.timestep(sigma)
        cfg_scale = extra_args['cfg_scale']
        eps_positive = self.unet(x_ddim_space, t, return_dict=False, **extra_args['positive'])[0]
        eps_negative = self.unet(x_ddim_space, t, return_dict=False, **extra_args['negative'])[0]
        noise_pred = eps_negative + cfg_scale * (eps_positive - eps_negative)
        return x - noise_pred * sigma[:, None, None, None]


class OmostSelfAttnProcessor:
    def __call__(self, attn, hidden_states, encoder_hidden_states, hidden_states_original_shape, *args, **kwargs):
        batch_size, sequence_length, _ = hidden_states.shape

        query = attn.to_q(hidden_states)
        key = attn.to_k(hidden_states)
        value = attn.to_v(hidden_states)

        inner_dim = key.shape[-1]
        head_dim = inner_dim // attn.heads

        query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)

        hidden_states = torch.nn.functional.scaled_dot_product_attention(
            query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False
        )

        hidden_states = hidden_states.transpose(1, 2).reshape(batch_size, -1, attn.heads * head_dim)
        hidden_states = hidden_states.to(query.dtype)
        hidden_states = attn.to_out[0](hidden_states)
        hidden_states = attn.to_out[1](hidden_states)

        return hidden_states


class OmostCrossAttnProcessor:
    def __call__(self, attn, hidden_states, encoder_hidden_states, hidden_states_original_shape, *args, **kwargs):
        B, C, H, W = hidden_states_original_shape

        conds = []
        masks = []

        for m, c in encoder_hidden_states:
            m = torch.nn.functional.interpolate(m[None, None, :, :], (H, W), mode='nearest-exact').flatten().unsqueeze(1).repeat(1, c.size(1))
            conds.append(c)
            masks.append(m)

        conds = torch.cat(conds, dim=1)
        masks = torch.cat(masks, dim=1)

        mask_bool = masks > 0.5
        mask_scale = (H * W) / torch.sum(masks, dim=0, keepdim=True)

        batch_size, sequence_length, _ = conds.shape

        query = attn.to_q(hidden_states)
        key = attn.to_k(conds)
        value = attn.to_v(conds)

        inner_dim = key.shape[-1]
        head_dim = inner_dim // attn.heads

        query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)

        mask_bool = mask_bool[None, None, :, :].repeat(query.size(0), query.size(1), 1, 1)
        mask_scale = mask_scale[None, None, :, :].repeat(query.size(0), query.size(1), 1, 1)

        sim = query @ key.transpose(-2, -1) * attn.scale
        sim = sim * mask_scale.to(sim)
        sim.masked_fill_(mask_bool.logical_not(), float("-inf"))
        sim = sim.softmax(dim=-1)

        h = sim @ value
        h = h.transpose(1, 2).reshape(batch_size, -1, attn.heads * head_dim)

        h = attn.to_out[0](h)
        h = attn.to_out[1](h)
        return h


class StableDiffusionXLOmostPipeline(StableDiffusionXLImg2ImgPipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k_model = KModel(unet=self.unet)

        attn_procs = {}
        for name in self.unet.attn_processors.keys():
            if name.endswith("attn2.processor"):
                attn_procs[name] = OmostCrossAttnProcessor()
            else:
                attn_procs[name] = OmostSelfAttnProcessor()

        self.unet.set_attn_processor(attn_procs)
        return

    @torch.inference_mode()
    def encode_bag_of_subprompts_greedy(self, prefixes: list[str], suffixes: list[str]):
        device = self.text_encoder.device

        @torch.inference_mode()
        def greedy_partition(items, max_sum):
            bags = []
            current_bag = []
            current_sum = 0

            for item in items:
                num = item['length']
                if current_sum + num > max_sum:
                    if current_bag:
                        bags.append(current_bag)
                    current_bag = [item]
                    current_sum = num
                else:
                    current_bag.append(item)
                    current_sum += num

            if current_bag:
                bags.append(current_bag)

            return bags

        @torch.inference_mode()
        def get_77_tokens_in_torch(subprompt_inds, tokenizer):
            # Note that all subprompt are theoretically less than 75 tokens (without bos/eos)
            result = [tokenizer.bos_token_id] + subprompt_inds[:75] + [tokenizer.eos_token_id] + [tokenizer.pad_token_id] * 75
            result = result[:77]
            result = torch.tensor([result]).to(device=device, dtype=torch.int64)
            return result

        @torch.inference_mode()
        def merge_with_prefix(bag):
            merged_ids_t1 = copy.deepcopy(prefix_ids_t1)
            merged_ids_t2 = copy.deepcopy(prefix_ids_t2)

            for item in bag:
                merged_ids_t1.extend(item['ids_t1'])
                merged_ids_t2.extend(item['ids_t2'])

            return dict(
                ids_t1=get_77_tokens_in_torch(merged_ids_t1, self.tokenizer),
                ids_t2=get_77_tokens_in_torch(merged_ids_t2, self.tokenizer_2)
            )

        @torch.inference_mode()
        def double_encode(pair_of_inds):
            inds = [pair_of_inds['ids_t1'], pair_of_inds['ids_t2']]
            text_encoders = [self.text_encoder, self.text_encoder_2]

            pooled_prompt_embeds = None
            prompt_embeds_list = []

            for text_input_ids, text_encoder in zip(inds, text_encoders):
                prompt_embeds = text_encoder(text_input_ids, output_hidden_states=True)

                # Only last pooler_output is needed
                pooled_prompt_embeds = prompt_embeds.pooler_output

                # "2" because SDXL always indexes from the penultimate layer.
                prompt_embeds = prompt_embeds.hidden_states[-2]
                prompt_embeds_list.append(prompt_embeds)

            prompt_embeds = torch.concat(prompt_embeds_list, dim=-1)
            return prompt_embeds, pooled_prompt_embeds

        # Begin with tokenizing prefixes

        prefix_length = 0
        prefix_ids_t1 = []
        prefix_ids_t2 = []

        for prefix in prefixes:
            ids_t1 = self.tokenizer(prefix, truncation=False, add_special_tokens=False).input_ids
            ids_t2 = self.tokenizer_2(prefix, truncation=False, add_special_tokens=False).input_ids
            assert len(ids_t1) == len(ids_t2)
            prefix_length += len(ids_t1)
            prefix_ids_t1 += ids_t1
            prefix_ids_t2 += ids_t2

        # Then tokenizing suffixes

        allowed_suffix_length = 75 - prefix_length
        suffix_targets = []

        for subprompt in suffixes:
            # Note that all subprompt are theoretically less than 75 tokens (without bos/eos)
            # So we can safely just crop it to 75
            ids_t1 = self.tokenizer(subprompt, truncation=False, add_special_tokens=False).input_ids[:75]
            ids_t2 = self.tokenizer_2(subprompt, truncation=False, add_special_tokens=False).input_ids[:75]
            assert len(ids_t1) == len(ids_t2)
            suffix_targets.append(dict(
                length=len(ids_t1),
                ids_t1=ids_t1,
                ids_t2=ids_t2
            ))

        # Then merge prefix and suffix tokens

        suffix_targets = greedy_partition(suffix_targets, max_sum=allowed_suffix_length)
        targets = [merge_with_prefix(b) for b in suffix_targets]

        # Encode!

        conds, poolers = [], []

        for target in targets:
            cond, pooler = double_encode(target)
            conds.append(cond)
            poolers.append(pooler)

        conds_merged = torch.concat(conds, dim=1)
        poolers_merged = poolers[0]

        return dict(cond=conds_merged, pooler=poolers_merged)

    @torch.inference_mode()
    def all_conds_from_canvas(self, canvas_outputs, negative_prompt):
        mask_all = torch.ones(size=(90, 90), dtype=torch.float32)
        negative_cond, negative_pooler = self.encode_cropped_prompt_77tokens(negative_prompt)
        negative_result = [(mask_all, negative_cond)]

        positive_result = []
        positive_pooler = None

        for item in canvas_outputs['bag_of_conditions']:
            current_mask = torch.from_numpy(item['mask']).to(torch.float32)
            current_prefixes = item['prefixes']
            current_suffixes = item['suffixes']

            current_cond = self.encode_bag_of_subprompts_greedy(prefixes=current_prefixes, suffixes=current_suffixes)

            if positive_pooler is None:
                positive_pooler = current_cond['pooler']

            positive_result.append((current_mask, current_cond['cond']))

        return positive_result, positive_pooler, negative_result, negative_pooler

    @torch.inference_mode()
    def encode_cropped_prompt_77tokens(self, prompt: str):
        device = self.text_encoder.device
        tokenizers = [self.tokenizer, self.tokenizer_2]
        text_encoders = [self.text_encoder, self.text_encoder_2]

        pooled_prompt_embeds = None
        prompt_embeds_list = []

        for tokenizer, text_encoder in zip(tokenizers, text_encoders):
            text_input_ids = tokenizer(
                prompt,
                padding="max_length",
                max_length=tokenizer.model_max_length,
                truncation=True,
                return_tensors="pt",
            ).input_ids

            prompt_embeds = text_encoder(text_input_ids.to(device), output_hidden_states=True)

            # Only last pooler_output is needed
            pooled_prompt_embeds = prompt_embeds.pooler_output

            # "2" because SDXL always indexes from the penultimate layer.
            prompt_embeds = prompt_embeds.hidden_states[-2]
            prompt_embeds_list.append(prompt_embeds)

        prompt_embeds = torch.concat(prompt_embeds_list, dim=-1)
        prompt_embeds = prompt_embeds.to(dtype=self.unet.dtype, device=device)

        return prompt_embeds, pooled_prompt_embeds

    @torch.inference_mode()
    def __call__(
            self,
            initial_latent: torch.FloatTensor = None,
            strength: float = 1.0,
            num_inference_steps: int = 25,
            guidance_scale: float = 5.0,
            batch_size: Optional[int] = 1,
            generator: Optional[Union[torch.Generator, List[torch.Generator]]] = None,
            prompt_embeds: Optional[torch.FloatTensor] = None,
            negative_prompt_embeds: Optional[torch.FloatTensor] = None,
            pooled_prompt_embeds: Optional[torch.FloatTensor] = None,
            negative_pooled_prompt_embeds: Optional[torch.FloatTensor] = None,
            cross_attention_kwargs: Optional[dict] = None,
    ):

        device = self.unet.device
        cross_attention_kwargs = cross_attention_kwargs or {}

        # Sigmas

        sigmas = self.k_model.get_sigmas_karras(int(num_inference_steps / strength))
        sigmas = sigmas[-(num_inference_steps + 1):].to(device)

        # Initial latents

        _, C, H, W = initial_latent.shape
        noise = randn_tensor((batch_size, C, H, W), generator=generator, device=device, dtype=self.unet.dtype)
        latents = initial_latent.to(noise) + noise * sigmas[0].to(noise)

        # Shape

        height, width = latents.shape[-2:]
        height = height * self.vae_scale_factor
        width = width * self.vae_scale_factor

        add_time_ids = list((height, width) + (0, 0) + (height, width))
        add_time_ids = torch.tensor([add_time_ids], dtype=self.unet.dtype)
        add_neg_time_ids = add_time_ids.clone()

        # Batch

        latents = latents.to(device)
        add_time_ids = add_time_ids.repeat(batch_size, 1).to(device)
        add_neg_time_ids = add_neg_time_ids.repeat(batch_size, 1).to(device)
        prompt_embeds = [(k.to(device), v.repeat(batch_size, 1, 1).to(noise)) for k, v in prompt_embeds]
        negative_prompt_embeds = [(k.to(device), v.repeat(batch_size, 1, 1).to(noise)) for k, v in negative_prompt_embeds]
        pooled_prompt_embeds = pooled_prompt_embeds.repeat(batch_size, 1).to(noise)
        negative_pooled_prompt_embeds = negative_pooled_prompt_embeds.repeat(batch_size, 1).to(noise)

        # Feeds

        sampler_kwargs = dict(
            cfg_scale=guidance_scale,
            positive=dict(
                encoder_hidden_states=prompt_embeds,
                added_cond_kwargs={"text_embeds": pooled_prompt_embeds, "time_ids": add_time_ids},
                cross_attention_kwargs=cross_attention_kwargs
            ),
            negative=dict(
                encoder_hidden_states=negative_prompt_embeds,
                added_cond_kwargs={"text_embeds": negative_pooled_prompt_embeds, "time_ids": add_neg_time_ids},
                cross_attention_kwargs=cross_attention_kwargs
            )
        )

        # Sample

        results = sample_dpmpp_2m(self.k_model, latents, sigmas, extra_args=sampler_kwargs, disable=False)

        return StableDiffusionXLPipelineOutput(images=results)
    
def main():
    # 1) Load & move the official SDXL Img2Img pipeline
    base = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float32
    ).to("cuda")                        # <-- move all base modules to GPU

    # 2) Instantiate your subclass using those GPU-resident modules
    pipeline = StableDiffusionXLOmostPipeline(
        vae=base.vae,
        image_encoder=base.image_encoder,
        text_encoder=base.text_encoder,
        text_encoder_2=base.text_encoder_2,
        tokenizer=base.tokenizer,
        tokenizer_2=base.tokenizer_2,
        unet=base.unet,
        scheduler=base.scheduler,
        feature_extractor=base.feature_extractor,
    )
    # <— NO .to("cuda") here!

    # 3) Build & process your Canvas
    canvas = Canvas()
    canvas.set_global_description(
        "A serene mountain landscape at sunrise",
        ["snow-capped peaks", "warm orange sky", "soft mist in the valley"],
        "landscape, nature, sunrise",
        "skyblue",
    )
    canvas.add_local_description(
        location="on the bottom-right",
        offset="no offset",
        area="a medium-sized square area",
        distance_to_viewer=5.0,
        description="A small wooden cabin by the lakeshore",
        detailed_descriptions=["warm light inside", "smoke rising from chimney"],
        tags="cabin, cozy",
        atmosphere="peaceful",
        style="photorealistic",
        quality_meta="8k, high detail",
        HTML_web_color_name="brown",
    )
    canvas_outputs = canvas.process()

    # 4) Prep the latent
    init = (
        torch.from_numpy(canvas_outputs["initial_latent"])
             .permute(2, 0, 1)
             .unsqueeze(0)
             .to(torch.float32)
             .to("cuda")
    )

    # 5) Encode conditions & sample
    positive, pos_pooler, negative, neg_pooler = pipeline.all_conds_from_canvas(
        canvas_outputs,
        negative_prompt="low resolution, blurry"
    )
    out = pipeline(
        initial_latent=init,
        strength=1.0,
        num_inference_steps=50,
        guidance_scale=7.5,
        batch_size=1,
        prompt_embeds=positive,
        negative_prompt_embeds=negative,
        pooled_prompt_embeds=pos_pooler.to("cuda"),
        negative_pooled_prompt_embeds=neg_pooler.to("cuda"),
    )

    # 6) Save result
    image: Image.Image = out.images[0]
    image.save("generated_image.png")
    print("✅ Image saved to generated_image.png")

if __name__ == "__main__":
    main()