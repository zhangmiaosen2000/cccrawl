
# import asyncio  
# from playwright.async_api import async_playwright  
import cv2, os
import numpy as np
import random 

async def draw_bounding_boxes(image_path, bounding_boxes):  
    # 读取图片  
    image = cv2.imread(image_path)  
  
    if image is None:  
        print("Could not open or find the image")  
        return  
  
    # 设置颜色和粗细  
    color = (0, 0, 255)  # 红色 (BGR格式)  
    thickness = 2  # 线条粗细  
  
    # 绘制每个bounding box  
    for box in bounding_boxes:  
        x1, y1, w, h = box["x"], box["y"], box["width"], box["height"]  
        x2, y2 = x1 + w, y1 + h  
        try:  
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)  
        except:  
            pass  
  
    # 显示图片  
    cv2.imwrite("screenshot_bbox.png", image)  

async def bbox_dedup(elements):
    bboxes = sorted(elements, key=lambda x: x["boundingBox"]["x"]*1e10+x["boundingBox"]["y"])
    cleaned = [bboxes[0]]
    for i in range(1, len(bboxes)-1):
        last_bbox = cleaned[-1]
        bbox = bboxes[i]
        # iou
        x1min, y1min = last_bbox["boundingBox"]['x'], last_bbox["boundingBox"]['y']
        x1max, y1max = last_bbox["boundingBox"]['x'] + last_bbox["boundingBox"]['width'], last_bbox["boundingBox"]['y'] + last_bbox["boundingBox"]['height']
        s1 = last_bbox["boundingBox"]['width'] * last_bbox["boundingBox"]['height']
        x2min, y2min = bbox["boundingBox"]['x'], bbox["boundingBox"]['y']
        x2max, y2max = bbox["boundingBox"]['x'] + bbox["boundingBox"]['width'], bbox["boundingBox"]['y'] + bbox["boundingBox"]['height']
        s2 = bbox["boundingBox"]['width'] * bbox["boundingBox"]['height']
        xmin = np.maximum(x1min, x2min)  # 左上角的横坐标
        ymin = np.maximum(y1min, y2min)  # 左上角的纵坐标
        xmax = np.minimum(x1max, x2max)  # 右下角的横坐标
        ymax = np.minimum(y1max, y2max)  # 右下角的纵坐标

        inter_h = np.maximum(ymax - ymin, 0.)
        inter_w = np.maximum(xmax - xmin, 0.)
        intersection = inter_h * inter_w

        union = s1 + s2 - intersection
        iou = intersection / union

        if iou > 0.6:
            continue
        else:
            cleaned.append(bbox)
    return cleaned

async def get_random_screen():
    area = random.choice(["1080p", "2.5k", "4k"])
    if area == "1080p":
        commonly_used_screen = {
            (1000+k*40, 2000-k*40): 0.033 for k in range(26)
        }
        commonly_used_screen[(1920, 1080)] += 0.142
    elif area == "2.5k":
        commonly_used_screen = {
            (1320+k*40, 2680-k*40): 0.027 for k in range(35)
        }
        commonly_used_screen[(2560, 1440)] += 0.055
    else:
        commonly_used_screen = {
            (2000+k*40, 4000-k*40): 0.019 for k in range(51)
        }
        commonly_used_screen[(3840, 2160)] += 0.031

    keys = list(commonly_used_screen.keys())  
    weights = list(commonly_used_screen.values())  
    # Sample a key based on the weights  
    reso = random.choices(keys, weights=weights, k=1)[0]  
    return reso


# from PIL import Image
# import torch
# import torch.nn.functional as F
# from dreamsim import dreamsim
# device = "cuda"
# model, preprocess = dreamsim(pretrained=True, device=device)


# async def get_norm(save_path, screen_shot_path, page_path):
#     img = preprocess(Image.open(save_path)).to("cuda")
#     layout_emb = model.embed(img)
#     layout_emb = F.normalize(layout_emb)
#     img = preprocess(Image.open(screen_shot_path)).to("cuda")
#     screen_emb = model.embed(img)
#     screen_emb = F.normalize(screen_emb)

#     layout_emb_path = os.path.join(page_path, "layout_emb.pth")
#     torch.save(layout_emb, layout_emb_path)
#     screen_emb_path = os.path.join(page_path, "screen_emb.pth")
#     torch.save(screen_emb, screen_emb_path)
#     return screen_emb, layout_emb


async def get_layout(elements, page_path, screen_shot_path, viewport_width, viewport_height):
    sorted_element = sorted(elements, key=lambda elem: elem["boundingBox"]["width"] * elem["boundingBox"]["height"] + 1e10*(1-int(elem["HasEventAttribute"] or elem["IsInteractiveTag"])), reverse=True)
    # 读取图片  
    canvas = np.ones((viewport_height, viewport_width, 3), dtype=np.uint8) * 255
  
    # 设置颜色和粗细  
    colors = {
        True: {
            "text": (0, 0, 255),
            "image": (255, 0, 0),
            "other": (0, 255, 0)
        },
        False: {
            "text": (255, 165, 0),
            "image": (255, 255, 0),
            "other": (238,130,238)
        }
    }
    thickness = -1  # fill  

    for elem in sorted_element:
        modal = "other"
        if elem["IsIcon"] or elem["IsImageTag"]:
            modal = "image"
        elif len(elem["innerText"]) > 0:
            modal = "text"
        color = colors[elem["HasEventAttribute"] or elem["IsInteractiveTag"]][modal]
        x1, y1, w, h = elem["boundingBox"]["x"], elem["boundingBox"]["y"], elem["boundingBox"]["width"], elem["boundingBox"]["height"]
        if w * h == 0 or w * h > 0.3*viewport_width*viewport_height:  
            continue  
        x2, y2 = x1 + w, y1 + h 
        try:  
            cv2.rectangle(canvas, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)  
        except:  
            pass

    # 显示图片  
    save_path = os.path.join(page_path, "layout.png")
    cv2.imwrite(save_path, canvas)

    # await get_norm(save_path, screen_shot_path, page_path)

    