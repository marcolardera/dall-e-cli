import click
import os
import requests
import sys
import time

OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
IMAGE_GENERATION_ENDPOINT="https://api.openai.com/v1/images/generations"

MODELS={"dall-e-2", "dall-e-3"}
SIZES_2={"256x256", "512x512", "1024x1024"}
SIZES_3={"1024x1024", "1792x1024", "1024x1792"}
QUALITIES={"standard", "hd"}
STYLES={"vivid", "natural"}

def make_request(api_key: str, params: dict[str]) -> tuple[dict, int]:
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    r=requests.post(IMAGE_GENERATION_ENDPOINT, headers=headers, json=params)

    return (r.json(), r.status_code)

@click.command()
@click.argument("prompt", required=False, default="A random image")
@click.option("--model", "-m", "model", default="dall-e-3", type=click.Choice(list(MODELS)),
              help="Model in use")
@click.option("--number", "-n", "n", default=1, type=click.IntRange(1),
              help="Number of images to be generated")
@click.option("--size", "-si", "size", default="1024x1024",
              help="Size of the images")
@click.option("--quality", "-q", "quality", default="standard", type=click.Choice(list(QUALITIES)),
              help="Quality of the image")
@click.option("--style", "-st", "style", default="vivid", type=click.Choice(list(STYLES)),
              help="Style of the image")
@click.option("--download", "-d", "download", type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
              help="Set the optional folder to download the images")
@click.option("--pipe", "-p", "pipe", is_flag=True,
              help="Enable prompt piping")
def main(prompt, model, n, size, quality, style, download, pipe) -> None:

    if not OPENAI_API_KEY:
        print("Missing api key")
        sys.exit()

    if model=="dall-e-2" and size not in SIZES_2:
        print(f"Size {size} not available for model dall-e-2")
        sys.exit()
    if model=="dall-e-3" and size not in SIZES_3:
        print(f"Size {size} not available for model dall-e-3")
        sys.exit()
    
    params={}
    params["prompt"]=sys.stdin.read() if pipe else prompt
    params["model"]=model
    params["n"]=n if model=="dall-e-2" else 1 # dall-e-3 only supports one image per request
    params["size"]=size
    if model=="dall-e-3":
        # Only available for dall-e-3
        params["quality"]=quality
        params["style"]=style

    try:
        image_request=make_request(OPENAI_API_KEY, params)
    except Exception as e:
        print("Unable to perform the request: ", e)

    response=image_request[0]
    status_code=image_request[1]
    
    match status_code:
        case 200:
            ts=int(time.time())
            for i, img in enumerate(response["data"]):

                if download:
                    try:
                        r=requests.get(img["url"])
                    except Exception as e:
                        print(f"Unable to download image {i}: ", e)
                    filename=f"{ts}_{i}.png"
                    filepath=os.path.join(download, filename)
                    with open(filepath, "wb") as file:
                        file.write(r.content)
                    print(f"{i} -> {filepath} written")
                else:
                    print(img["url"])

        case 401:
            print("Invalid Authentication")
        case 429:
            print("Rate limit reached or personal quota excedeed")
        case 500:
            print("Internal server error")
        case 502|503:
            print("Server overloaded")
        case _:
            print(f"Unknown error, status code {status_code}")
            print(response)
    

if __name__ == "__main__":
    main()