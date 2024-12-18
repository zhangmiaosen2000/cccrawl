import asyncio  
from playwright.async_api import async_playwright  
import cv2  
import numpy as np  
import random  
from ccutils import get_random_screen, bbox_dedup, get_layout
import argparse  
import json, os
from tqdm.asyncio import tqdm  
from tqdm import tqdm as tqdm_sync  


async def process_page(page, web_idx, scroll_idx, args, viewport_width, viewport_height, url_info):
    unique_page_name = f"web_{web_idx}_scroll_{scroll_idx}"
    page_path = os.path.join(args.out_dir, args.run_name, unique_page_name)
    os.makedirs(page_path, exist_ok = True) 

    # 保存截图  
    screenshot_path = os.path.join(page_path, f'screenshot.png')
    await page.screenshot(path=screenshot_path)  
  
    elements = await page.evaluate('''() => {  
        const allElements = document.querySelectorAll('*');  
        const interactiveElements = [];  
        allElements.forEach(element => {  
            const tagName = element.tagName.toLowerCase();  
            const isInteractiveTag = ['button', 'input', 'textarea', 'select', 'a', 'form'].includes(tagName);  
            const hasEventAttribute = element.hasAttribute('onclick') || element.hasAttribute('onmousedown') || element.hasAttribute('onmouseup') || element.hasAttribute('onmouseover') || element.hasAttribute('onmouseout') || element.hasAttribute('onkeydown') || element.hasAttribute('onkeyup');  
            const hasRoleAttribute = element.hasAttribute('role') && ['button', 'link', 'textbox', 'menuitem', 'option', 'checkbox', 'radio', 'tab', 'switch'].includes(element.getAttribute('role'));  
            const className = element.className;  
            const isStringClassName = typeof className === 'string';  
            const hasInteractiveClass = isStringClassName && ['btn', 'button', 'input', 'link', 'nav', 'menu', 'item'].some(keyword => className.toLowerCase().includes(keyword));  
            const isImageTag = tagName === 'img'; 
            const notHTML = element.tagName !== 'HTML'; 
            const isString = (element.innerText !== '') && (element.tagName !== 'DIV');  
                    
            const isIcon = (tagName === 'i' || tagName === 'span' || tagName === 'svg') && (isStringClassName && ['fa', 'fas', 'far', 'fal', 'fab', 'material-icons'].some(keyword => className.toLowerCase().includes(keyword))) || (tagName === 'img' && element.getAttribute('src') && element.getAttribute('src').toLowerCase().includes('icon'));  
            if ((isInteractiveTag || hasEventAttribute || hasRoleAttribute || hasInteractiveClass || isImageTag || isIcon || isString) && notHTML) {  
                const rect = element.getBoundingClientRect();  
                interactiveElements.push({  
                    tag: element.tagName,  
                    boundingBox: {  
                        x: rect.x,  
                        y: rect.y,  
                        width: rect.width,  
                        height: rect.height  
                    },  
                    IsString: isString,
                    IsInteractiveTag: isInteractiveTag,  
                    HasEventAttribute: hasEventAttribute,  
                    HasRoleAttribute: hasRoleAttribute,  
                    HasInteractiveClass: hasInteractiveClass,  
                    IsImageTag: isImageTag,  
                    IsIcon: isIcon,  
                    outerHTML: element.outerHTML,  
                    innerText: element.innerText || '',  
                    placeholder: element.getAttribute('placeholder') || '',  
                    alt: element.getAttribute('alt') || '',  
                    title: element.getAttribute('title') || '',  
                    ariaLabel: element.getAttribute('aria-label') || '',  
                    ariaLabelledby: element.getAttribute('aria-labelledby') || ''  
                });  
            }  
        });  
        return interactiveElements;  
    }''')  
  
    # 过滤掉不在视口范围内的元素  
    filtered_elements = [elem for elem in elements if 0 <= elem["boundingBox"]["x"] <= viewport_width and 0 <= elem["boundingBox"]["y"] <= viewport_height]  
    filtered_elements = [elem for elem in filtered_elements if elem["boundingBox"]["width"] * elem["boundingBox"]["height"] > 0]  
    filtered_elements = await bbox_dedup(filtered_elements)  
    
    info_path = os.path.join(page_path, f'info.json')
    info = dict(elements = filtered_elements, width = viewport_width, height = viewport_height)
    info.update(url_info)
    open(info_path, "w").write(json.dumps(info, indent=4))

    await get_layout(filtered_elements, page_path, screenshot_path, viewport_width, viewport_height)
    return True

async def process_url(browser, url_info, idx, args, progress):  
    url = url_info["url"]  
    # 设置浏览器视口大小  
    viewport_width, viewport_height = await get_random_screen()  
    context = await browser.new_context(viewport={'width': viewport_width, 'height': viewport_height}, ignore_https_errors=True)  
    page = await context.new_page()  
    retry_attempts = 3  
    for attempt in range(retry_attempts):  
        try:  
            await page.goto(url, timeout=10000) 
            await page.wait_for_load_state('load')  
            await page.wait_for_timeout(2000)  # 等待2秒  
  
            # 获取页面总高度  
            total_height = await page.evaluate('document.body.scrollHeight')  
            # 计算需要滚动的次数  
            num_scrolls = min(total_height // viewport_height, 5)  
  
            for scroll_idx in range(num_scrolls):  
                await process_page(page, idx, scroll_idx, args, viewport_width, viewport_height, url_info)  
                # 滚动页面  
                await page.evaluate(f'window.scrollBy(0, {viewport_height})')  
                await page.wait_for_timeout(2000)  # 等待2秒让页面滚动完成  
            break  # Break the loop if successful  
        except Exception as e:  
            if attempt < retry_attempts - 1:  
                continue
                # print(f"Retrying {url} (attempt {attempt + 1}/{retry_attempts}) due to error: {e}")  
            else:  
                # print(f"Failed to process {url} after {retry_attempts} attempts: {e}")  
                for i in range(3):  
                    unique_page_name = f"web_{idx}_scroll_{i}"  
                    page_path = os.path.join(args.out_dir, args.run_name, unique_page_name)  
                    if os.path.exists(page_path):  
                        os.system(f"rm -rf {page_path}")  
     
    await context.close()  
    progress.update(1)  
  
async def main():  
    parser = argparse.ArgumentParser()  
    parser.add_argument("--index", type = str)
    parser.add_argument("--out-dir", type = str)
    parser.add_argument("--run-name", type = str)
    parser.add_argument("--start", type = int)
    parser.add_argument("--end", type = int)
    args = parser.parse_args()
    jsl = json.load(open(args.index))
    stid = int(100000*args.start)
    endid = int(100000*args.end)
    batch_max = 100
    print(f"running index from {stid} to {endid}")
    for idx in range((endid-stid)//batch_max):
        print(idx)
        async with async_playwright() as p:  
            browser = await p.chromium.launch(headless=True)  
            urls = jsl[stid + idx * batch_max: stid + (idx+1) * batch_max]

            with tqdm_sync(total=len(urls), desc="Processing URLs") as progress:  
                tasks = [process_url(browser, url, stid + idx * batch_max + iidx, args, progress) for iidx, url in enumerate(urls)]  
                await asyncio.gather(*tasks) 
    
            await browser.close()  
  
if __name__ == "__main__":  
    # 运行主函数  
    asyncio.run(main())  