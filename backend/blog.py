
from fastapi import APIRouter, File, Request, Response, Cookie, UploadFile
from typing import List
from datetime import datetime
import shutil
import sys
import os

router = APIRouter()

PARENT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(1, os.path.join(PARENT_DIRECTORY, "data"))

from content import Blog
from database import *
from auth.auth_handler import decodeJWT
        
if not os.path.exists("uploads"):
    os.makedirs("uploads")

@router.post("/createBlog/", tags=["blog"])
async def createBlog(response: Response, request: Request, title: str, text: str, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        if not userId in root.user:
            raise Exception("author not found")
            
        mediaID = list()
        
        root.blog[root.config["currentBlogID"]] = Blog(root.config["currentBlogID"], title, userId, text, mediaID)
        root.user[userId].createBlog(root.config["currentBlogID"])
        
        root.config["currentBlogID"] += 1
        transaction.commit()
        
        return root.blog[root.config["currentBlogID"] - 1]
    except Exception as e:
        return {"detail": str(e)}

@router.post("/createBlogWithMedia/", tags=["blog"])
async def createBlogWithMedia(response: Response, request: Request, title: str, text: str, media: List[UploadFile] = File(...), access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        if not userId in root.user:
            raise Exception("author not found")
        
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
            
        mediaID = list()
        for file in media:
            file_path = os.path.join("uploads", str(root.config["currentMediaID"]) + "." + file.filename.split(".")[-1])
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            mediaID.append(root.config["currentMediaID"])
            root.config["currentMediaID"] += 1
        
        root.blog[root.config["currentBlogID"]] = Blog(root.config["currentBlogID"], title, userId, text, mediaID)
        root.user[userId].createBlog(root.config["currentBlogID"])
        
        root.config["currentBlogID"] += 1
        transaction.commit()
        
        return root.blog[root.config["currentBlogID"] - 1]
    except Exception as e:
        return {"detail": str(e)}

@router.post("/removeBlog/", tags=["blog"])
async def removeBlog(response: Response, request: Request, blogID: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        if not userId in root.user:
            raise Exception("author not found")
        
        if not root.user[userId].deleteBlog(blogID):
            raise Exception("user has no permission")
        
        blog = root.blog[blogID]
        for mediaID in blog.media:
            if os.path.exists(os.path.join("uploads", str(mediaID)) + ".png"):
                os.remove(os.path.join("uploads", str(mediaID)) + ".png")
            elif os.path.exists(os.path.join("uploads", str(mediaID)) + ".jpg"):
                os.remove(os.path.join("uploads", str(mediaID)) + ".jpg")
            elif os.path.exists(os.path.join("uploads", str(mediaID)) + ".jpeg"):
                os.remove(os.path.join("uploads", str(mediaID)) + ".jpeg")
            elif os.path.exists(os.path.join("uploads", str(mediaID)) + ".MP4"):
                os.remove(os.path.join("uploads", str(mediaID)) + ".MP4")
            else:
                raise Exception("File not found in the db.")
        
        del root.blog[blogID]
        
        transaction.commit()
        
        return {"detail": f"successfully remove blog {blogID}"}
    except Exception as e:
        return {"detail": str(e)}
    
@router.post("/editBlog/", tags=["blog"])
async def editBlog(response: Response, request: Request, blogID: int, title: str, text: str, media: List[UploadFile] = File(...), access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        if not userId in root.user:
            raise Exception("author not found")
        
        if not root.user[userId].editBlog(blogID):
            raise Exception("user has no permission")
        
        mediaID = list()
        if media == None:
            for current in root.blog[blogID].media:
                if os.path.exists(os.path.join("uploads", str(current)) + ".png"):
                    os.remove(os.path.join("uploads", str(current)) + ".png")
                elif os.path.exists(os.path.join("uploads", str(current)) + ".jpg"):
                    os.remove(os.path.join("uploads", str(current)) + ".jpg")
                elif os.path.exists(os.path.join("uploads", str(current)) + ".jpeg"):
                    os.remove(os.path.join("uploads", str(current)) + ".jpeg")
                elif os.path.exists(os.path.join("uploads", str(current)) + ".MP4"):
                    os.remove(os.path.join("uploads", str(current)) + ".MP4")
                else:
                    raise Exception("File not found in the db.")
        else:
            temp = list()
            for file in media:
                filename, file_extension = os.path.splitext(file.filename)
                temp.append(filename)
                
            for current in root.blog[blogID].media:
                if not current in temp:
                    if os.path.exists(os.path.join("uploads", str(current)) + ".png"):
                        os.remove(os.path.join("uploads", str(current)) + ".png")
                    elif os.path.exists(os.path.join("uploads", str(current)) + ".jpg"):
                        os.remove(os.path.join("uploads", str(current)) + ".jpg")
                    elif os.path.exists(os.path.join("uploads", str(current)) + ".jpeg"):
                        os.remove(os.path.join("uploads", str(current)) + ".jpeg")
                    elif os.path.exists(os.path.join("uploads", str(current)) + ".MP4"):
                        os.remove(os.path.join("uploads", str(current)) + ".MP4")
                    else:
                        raise Exception("File not found in the db.")
            
            for file in media:
                filename, file_extension = os.path.splitext(file)
                if not filename in root.blog[blogID].media:
                    file_path = os.path.join("uploads", str(root.config["currentMediaID"]) + "." + file.filename.split(".")[-1])
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    mediaID.append(root.config["currentMediaID"])
                    root.config["currentMediaID"] += 1
                else:
                    mediaID.append(filename)
        
        root.blog[blogID].editContent(title, text, media)
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}
    
@router.post("/addLikeBlog/", tags=["blog"])
async def addLikeBlog(response: Response, request: Request, blogID: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        if userId in root.blog[blogID].like:
            return
        
        root.blog[blogID].addLike(userId)
        root.user[root.blog[blogID].author].addNotification(f"{root.user[userId].username} liked your blog, {root.blog[blogID].title}", datetime.now())
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}
    
@router.post("/removeLikeBlog/", tags=["blog"])
async def removeLikeBlog(response: Response, request: Request, blogID: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        if not userId in root.blog[blogID].like:
            return
        
        root.blog[blogID].removeLike(userId)
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}
    
@router.post("/addReplyBlog/", tags=["blog"])
async def addReplyBlog(response: Response, request: Request, blogID: int, text: str, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        root.blog[blogID].addReply(userId, text)
        root.user[root.blog[blogID].author].addNotification(f"{root.user[userId].username} replied to your blog, {root.blog[blogID].title}", datetime.now())
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}

@router.post("/addLikeReplyBlog/", tags=["blog"])
async def addLikeReplyBlog(response: Response, request: Request, blogID: int, replyIndex: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        if userId in root.blog[blogID].reply[replyIndex].like:
            return
            
        root.blog[blogID].reply[replyIndex].addLike(userId)
        root.user[root.blog[blogID].reply[replyIndex].author].addNotification(f"{root.user[userId].username} liked your reply in {root.blog[blogID].title}", datetime.now())
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}

@router.post("/removeLikeReplyBlog/", tags=["blog"])
async def removeLikeReplyBlog(response: Response, request: Request, blogID: int, replyIndex: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        if not userId in root.blog[blogID].reply[replyIndex].like:
            return
            
        root.blog[blogID].reply[replyIndex].removeLike(userId)
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}

@router.post("/removeReplyBlog/", tags=["blog"])
async def removeReplyBlog(response: Response, request: Request, blogID: int, replyIndex: int, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        userId = token["userId"]
        
        if not root.blog[blogID].removeReply(replyIndex, userId):
            raise Exception("user has no permission")
        
        transaction.commit()
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}
    
@router.get("/getBlog/", tags=["blog"])
async def getBlog(response: Response, request: Request, blogID: int):
    try:
        if not blogID in root.blog:
            raise Exception("blog not found")
        
        return root.blog[blogID]
    except Exception as e:
        return {"detail": str(e)}
    
@router.get("/getCurrentBlogID/", tags=["blog"])
async def getCurrentBlogID(response: Response, request: Request):
    return {"currentBlogID": root.config["currentBlogID"]}

@router.get("/getSortedBlogByLike", tags=["blog"])
async def getSortedBlogByLike(response: Response, request: Request):
    try:
        result = []
        for b in sorted(root.blog.values(), key=lambda blog: len(blog.like), reverse=True):
            result.append(b.blogID)
        
        return result
    except Exception as e:
        return {"detail": str(e)}