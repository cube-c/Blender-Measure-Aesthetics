# Measure Aesthetics

**Will People Like Your Render?**

This is a simple Blender3D add-on that measures image aesthetics based on technical parameters and attractiveness using Everypixel API.

![demo](https://user-images.githubusercontent.com/49553394/175886595-0c1b789d-cef4-48bb-965d-582375813b94.PNG)

## Setup

1. Download ZIP
2. Go to `Edit > Preferences > Add-ons > Install` and select downloaded ZIP file.
3. Create an [Everypixel account](https://labs.everypixel.com/api/register) and get API credentials. You can use the API for up to 100 images per day at no cost.
4. Go to add-on preferences and write down your ID and secret key.

![account](https://user-images.githubusercontent.com/49553394/175892404-ac87505c-ec36-4934-bb1e-d61ddb521209.PNG)

## Location

`Image Editor (or UV Editor) > Panel > Aesthetics`

## Features

* `Evaluate` : Measure aesthetics of the image.
* `Cache` : After the successful evaluation, the result is stored in the cache folder. 
  * It is possible to check the evaluation history by clicking the image preview. 

## Notes

* If the network is slow or the image is too large, Blender can stop for a long time.
* The API is far from perfect. Also, it may not be appropriate for non-photorealistic renders because this was originally designed to get the quality score for stock photos.
