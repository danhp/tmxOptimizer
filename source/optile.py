# Copyright (C) 2012 Guava7
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from xml.dom import minidom
import Image, ImageDraw
import zlib
import math
import os
import sys
import shutil
import ImageChops

def GetFileNX(long_file_path):
	return os.path.basename(long_file_path)


def GetFileN(long_file_path):
	filename = GetFileNX(long_file_path)
	return os.path.splitext(filename)[0]
	
def GetFileX(long_file_path):
	filename = GetFileNX(long_file_path)
	return os.path.splitext(filename)[1]

gTilesetMapping = {}
gTilesetDuplicate = {}
gTilesetItemCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
gKeepTileset = []

def convertMap(tmx, time_count):
	global gTilesetMapping
	global gTilesetItemCount
	global gTilesetDuplicate
	doc = minidom.parse(tmx)
	tilemap  = doc.getElementsByTagName("map")[0]
	width = int(tilemap.getAttribute("width"))
	height = int(tilemap.getAttribute("height"))
	
	re_data = {'width':width, 'height':height, 'numLayer': 0,'layers_data': [], 'layers_type':[], 'numTileset':0, 'tilesets':[]}
	
	def findLayer(tileID):
		
		global gTilesetMapping
		global gTilesetItemCount
		global gTilesetDuplicate
		for tileset in re_data['tilesets']:
			if tileset['firstgid'] <= tileID and tileset['lastgid'] >= tileID:
				# print("findLayer", tileID, tileset['index'], tileID - tileset['firstgid'], 0)
				if tileset['keep'] == False:
					gTilesetMapping[tileID] = [tileset['index'], tileID - tileset['firstgid'], 0]
				else:
					gTilesetMapping[tileID] = [tileset['index'], tileID - tileset['firstgid'], tileID - tileset['firstgid']]
				return
	
	for node in tilemap.childNodes:
		if node.nodeName == "layer":
			layerdata = node.getElementsByTagName("data")[0].childNodes[0].data
			layerdata = layerdata.decode('base64').decode('zlib')
			array = []
			lord = ord
			layerdata_append = array.append
			__i = 0
			tmp_num = 0
			for number in map(lord, layerdata):
				tmp_num += (number<<(__i))
				__i += 8
				if __i == 32:
					if tmp_num != 0:
						if gTilesetDuplicate.has_key(tmp_num):
							tmp_num = gTilesetDuplicate[tmp_num]
						# if gTilesetDuplicate.has_key(tmp_num):
							# print(tmp_num, gTilesetDuplicate[tmp_num])
							# tmp_num = gTilesetDuplicate[tmp_num]
						# else:
							# print(tmp_num)
						findLayer(tmp_num)
					layerdata_append(tmp_num)
					__i = 0
					tmp_num = 0
			
			re_data['layers_data'].append(array)
			re_data['layers_type'].append("layer")
			re_data['numLayer'] = re_data['numLayer'] + 1
		
		elif node.nodeName == "objectgroup":
			# echo("objectgroup")
			# print(node.childNodes.child)
			objlist = []
			for obj in node.getElementsByTagName("object"):
				objConv = {
					'x': obj.getAttribute("x"), 
					'y': obj.getAttribute("y"), 
					'width': obj.getAttribute("width"), 
					'height': obj.getAttribute("height"), 
					'name': obj.getAttribute("name"),
					'gid': obj.getAttribute("gid")
				}
				# print(objConv)
				objlist.append(objConv)
				if objConv['gid'] != "":
					findLayer(int(obj.getAttribute("gid")))
			re_data['layers_data'].append(objlist)
			re_data['layers_type'].append("objectgroup")
			re_data['numLayer'] = re_data['numLayer'] + 1
			
		elif node.nodeName == "tileset":
			tilesetObj = {
				'firstgid' : int(node.getAttribute("firstgid")), 
				'name' : node.getAttribute("name"), 
				'tilewidth' : int(node.getAttribute("tilewidth")), 
				'tileheight' : int(node.getAttribute("tileheight")), 
				'image' : node.childNodes[1].getAttribute("source"),
				'imageW' : node.childNodes[1].getAttribute("width"),
				'imageH' : node.childNodes[1].getAttribute("height"),
				'lastgid': 0,
				'index' : re_data['numTileset'],
				'keep': False,
			}
			re_data['numTileset'] += 1
			imgw = int(node.childNodes[1].getAttribute("width"))
			imgh = int(node.childNodes[1].getAttribute("height"))
			numOfTile = int(imgw/tilesetObj['tilewidth']) * int(imgh/tilesetObj['tileheight'])
			tilesetObj['lastgid'] = tilesetObj['firstgid'] + numOfTile - 1
			tilesetObj['keep'] = tilesetObj['image'] in gKeepTileset
			re_data['tilesets'].append(tilesetObj)
			if tilesetObj['keep'] == True:
				# print("xxx", tilesetObj['index'], re_data['numTileset'])
				gTilesetItemCount[tilesetObj['index']] = numOfTile
			# print(tilesetObj['keep'], tilesetObj['image'], gKeepTileset, tilesetObj['keep'] in gKeepTileset)
			else:
				if time_count == 0: # run once
					#check if duplicate tile
					img_src = Image.open(tilesetObj['image'])
					tilew = int(tilesetObj['tilewidth'])
					tileh = int(tilesetObj['tileheight'])
					imgw = int(tilesetObj['imageW'])
					imgh = int(tilesetObj['imageH'])
					numOfCols = int(imgw/tilew)
					numOfRows = int(imgh/tileh)
					firstID = tilesetObj['firstgid']
					# print(firstID)
					
					tiles = []
					tmpx = 0
					tmpy = 0
					
					for r in range(numOfRows):
						tmpx = 0
						for c in range (numOfCols):
							box = (tmpx, tmpy, tmpx + tilew, tmpy + tileh)
							region = img_src.crop(box)
							# region.load()
							img_des = Image.new('RGBA', (tilew, tileh))
							img_des.paste(region, (0, 0))
							
							# print(box)
							# img_des.save("./tmp/" + tilesetObj['image'] + "_id_" + str(firstID + c + r*numOfCols) + ".png")
							
							tmp = [firstID + c + r*numOfCols, tmpx, tmpy, tilew, tileh, img_des]
							tiles.append(tmp)
							tmpx += tilew
						tmpy += tileh
					
					checking = []
					dup_count = 0
					
					for src in tiles:
						match_index = -1
						region_src = src[5]
						for cmp in checking:
							region_cmp = cmp[5]
							found = ImageChops.difference(region_src, region_cmp).getbbox() is None
							if found:	
								match_index = cmp[0]
								break
						if match_index >= 0:
							gTilesetDuplicate[src[0]] = match_index
							dup_count += 1
						else:
							checking.append([src[0], src[1], src[2], src[3], src[4], src[5]])
					print("	Duplicate tiles in " + tilesetObj['image'] + " : " + str(dup_count) + "/" + str(len(tiles)))
	# if time_count == 0: print(gTilesetDuplicate)
	return re_data
	
def CommonProcess(re_data):		
	global gTilesetMapping
	global gTilesetItemCount
	
	# count tilest in tiles
	# gTilesetItemCount = []
	for key in sorted(gTilesetMapping.iterkeys()):
		itemInfo = gTilesetMapping[key]
		tilesetIndex = itemInfo[0]
		if re_data['tilesets'][tilesetIndex]['keep'] == False:
			itemInfo[2] = gTilesetItemCount[tilesetIndex]
			gTilesetItemCount[tilesetIndex] += 1
	# print(gTilesetMapping)
	
	# modify tilesetImage	
	tmp_index = 0
	for tmp_index in range(len(re_data['tilesets'])):
		tileset = re_data['tilesets'][tmp_index]
		_tmp_imagename  = tileset['image']
		# print(_tmp_imagename)
		img_src = Image.open(_tmp_imagename)
		if tileset['keep'] == True:
			# print(tileset)
			img_src.save("./output/" + tileset['image'], optimize=1)
		else:
			_tmpsize = gTilesetItemCount[tmp_index]
			# print(_tmpsize)
			if _tmpsize > 0:
				tmp_index += 1
				_tmpsize = math.sqrt(_tmpsize)
				# print(_tmpsize)
				if _tmpsize - int(_tmpsize) == 0:
					_tmpsize = int(_tmpsize)
				else:
					_tmpsize = int(_tmpsize) + 1
				image_w, image_h = img_src.size
				sizew = _tmpsize * tileset['tilewidth']
				sizeh = _tmpsize * tileset['tileheight']
				runlen = int(image_w / tileset['tilewidth'])
				img_des = Image.new('RGBA', (sizew, sizeh))

				for key in sorted(gTilesetMapping.iterkeys()):
					itemInfo = gTilesetMapping[key]
					if itemInfo[0] == tileset['index']:
						fromTile = itemInfo[1]
						fromTile_r = int(fromTile / runlen)
						fromTile_c = int(fromTile % runlen)
						fromTile_x = fromTile_c*tileset['tilewidth']
						fromTile_y = fromTile_r*tileset['tileheight']
						toTile = itemInfo[2]
						toTile_r = int(toTile / _tmpsize)
						toTile_c = int(toTile % _tmpsize)
						toTile_x = toTile_c*tileset['tilewidth']
						toTile_y = toTile_r*tileset['tileheight']
						# print(_tmpsize, itemInfo[0], fromTile, toTile, toTile_r, toTile_c, toTile_x, toTile_y)
						
						# print(fromTile_x, fromTile_y, toTile_x, toTile_y)
						tmp = img_src.crop((fromTile_x, fromTile_y, fromTile_x + tileset['tilewidth'], fromTile_y + tileset['tileheight']))
						tmp.load()
						img_des.paste(tmp, (toTile_x, toTile_y))
				tileset['imageW'], tileset['imageH'] = img_des.size
				img_des.save("./output/" + tileset['image'], optimize=1)
			else:
				img_des = Image.new('RGBA', (1, 1))
				tileset['tilewidth'] = 1
				tileset['tileheight'] = 1
				tileset['imageW'], tileset['imageH'] = img_des.size
				img_des.save("./output/" + tileset['image'], optimize=1)
	return re_data['tilesets']
	
def IndividualProcess(tmx, re_data, tileset):
	re_data['tilesets'] = tileset
	global gTilesetMapping
	global gTilesetItemCount
	doc = minidom.parse(tmx)
	tilemap  = doc.getElementsByTagName("map")[0]
	# modify firstid
	tmp_count = 1
	tmp_index = 0
	for tileset in re_data['tilesets']:
		if gTilesetItemCount[tmp_index] == 0:
			tileset['firstgid'] = tmp_count
			tmp_count += 1
			tileset['lastgid'] = tmp_count - 1
			tmp_index += 1
		else:
			_tmpsize = gTilesetItemCount[tmp_index]
			_tmpsize = math.sqrt(_tmpsize)
			if _tmpsize - int(_tmpsize) == 0:
				_tmpsize = int(_tmpsize)
			else:
				_tmpsize = int(_tmpsize) + 1

			tileset['firstgid'] = tmp_count
			tmp_count += _tmpsize*_tmpsize
			tileset['lastgid'] = tmp_count - 1
			tmp_index += 1

	# modify cell id
	# print(gTilesetMapping)
	for i in range(re_data['numLayer']):
		if re_data['layers_type'][i] == "layer":
			tmp = re_data['layers_data'][i]
			for j in range(len(tmp)):
				if tmp[j] > 0:
					# print(tmp[j])
					itemInfo = gTilesetMapping[tmp[j]]
					tilesetID = itemInfo[0]
					tileIndex = itemInfo[2]
					firstTileID = re_data['tilesets'][tilesetID]['firstgid']
					tmp[j] = firstTileID + tileIndex
	
	# save new tilemap data
	layerIdx = 0
	tilesetIdx = 0
	def parseFunc(i):
		b1 = (i >> 24) & 255
		b2 = (i >> 16) & 255
		b3 = (i >> 8) & 255
		b4 = (i) & 255
		return "%s%s%s%s"%(chr(b4), chr(b3), chr(b2), chr(b1))
	for node in tilemap.childNodes:
		if node.nodeName == "layer":
			plain_data = re_data['layers_data'][layerIdx]
			# print(plain_data)
			layerIdx = layerIdx + 1
			txt_data = ""
			slist = [parseFunc(elt) for elt in plain_data]
			txt_data = "".join(slist)
			encode_data = txt_data.encode('zlib').encode('base64')
			node.getElementsByTagName("data")[0].childNodes[0].data = encode_data
		elif node.nodeName == "tileset":
			tileset = re_data['tilesets'][tilesetIdx]
			node.setAttribute("firstgid", str(tileset['firstgid']))
			node.childNodes[1].setAttribute("source", str(tileset['image']))
			node.childNodes[1].setAttribute("width", str(tileset['imageW']))
			node.childNodes[1].setAttribute("height", str(tileset['imageH']))
			tilesetIdx = tilesetIdx + 1
		elif node.nodeName == "objectgroup":
			for obj in node.getElementsByTagName("object"):
				gid = obj.getAttribute("gid")
				if gid != "":
					itemInfo = gTilesetMapping[int(gid)]
					tilesetID = itemInfo[0]
					tileIndex = itemInfo[2]
					firstTileID = re_data['tilesets'][tilesetID]['firstgid']
					obj.setAttribute("gid", str(tileIndex + firstTileID))
			layerIdx = layerIdx + 1
	f = open("./output/" + tmx, 'w')
	doc.writexml(f)
	f.close()
	# print(gTilesetItemCount)
	# print(re_data)
	# print(gTilesetMapping)
	# return re_data

def run(cnf):
	global gKeepTileset
	try:
		os.makedirs("./output")
	except OSError, e:
		str1 = raw_input("Output dir is already existed. Would you like to remove and continue [Y/N] : ")
		if str1 in ["y", "Y"]:
			try:
				shutil.rmtree('./output')
			except:
				print("[ERROR] Fail to remove output dir. Please remove it manually")
				sys.exit()
			os.makedirs("./output")
		else:
			print("CANCEL")
			sys.exit()
			
	input = cnf['input']
	keeptile = cnf['keep']
	
	gKeepTileset = keeptile
	conv = []
	if len(input) > 0:
		print("[Step 1] Collect map information")
		for i in range(len(input)):
			re = convertMap(input[i], i)
			conv.append(re)
		print("[Step 2] Adjust tileset data")
		tilset =  CommonProcess(conv[0])
		print("[Step 3] Export new map")
		for i in range(len(input)):
			IndividualProcess(input[i], conv[i], tilset)
	print("DONE!")

def LoadConfig(fn):
	doc = minidom.parse(fn)
	data  = doc.getElementsByTagName("config")[0]
	cnf = {}
	cnf['input'] = []
	cnf['keep'] = []
	for node in data.childNodes:
		if node.nodeName == "input":
			cnf['input'].append(node.getAttribute('file'))
		elif  node.nodeName == "keep":
			cnf['keep'].append(node.getAttribute('file'))
	return cnf
	
# LoadConfig("@optile_config.xml")
print("Tileset Optimize Tool. Version 1.1")
print("Copyright (C) 2012 Guava7")
run(LoadConfig("@optile_config.xml"))