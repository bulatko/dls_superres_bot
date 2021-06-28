import torch
from torch import nn
import sys
from torchvision import transforms as tt
import matplotlib.pyplot as plt
import numpy as np
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

sys.path.append('a-PyTorch-Tutorial-to-Super-Resolution')
from utils import *

def get_model():
    check_point = torch.load('checkpoint_srgan.pth.tar', map_location=torch.device('cpu'))
    net = check_point['generator'].eval()

    return net

def convert(img):
  return (img.permute(0, 2, 3, 1) + 1) / 2

def super_res_image(image_name, net):
    image = plt.imread(image_name)
    image_tensor = tt.Compose([tt.ToTensor(),
                        tt.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])(image)[None]
    h, w = image.shape[:2]
    interpolated_image = tt.Compose([
        tt.ToPILImage(),
        tt.Resize((h * 4, w * 4)),
        tt.ToTensor()
    ])((image  * 255).astype(np.uint8)).permute(1, 2, 0).numpy()
    
    plt.imsave('interpolated_' + image_name, interpolated_image)

    res = net(image_tensor)
    image = convert(res.detach())[0].numpy()
    plt.imsave(image_name, image)
    
def main_menu():
    buttons = [
        [
            'Улучшить изображение', 
            'Статистика'
        ]

    ]
    return create_simple_keyboard(buttons)

def create_simple_keyboard(array):
    res = ReplyKeyboardMarkup()
    for a in array:
        res.row(*a)
    
    return res
