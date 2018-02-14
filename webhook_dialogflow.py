from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import datetime

from flask import Flask
from flask import request
from flask import make_response, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def T0_Judge(string):
	if string=='':
		ans='U2'
	else:
		ans='U1'

	return ans

def T1_Judge(string):
	list_yes=['そう','はい','うん','言われた','言ってた']
	list_no=['いいえ','違う','ない','いや']

	for yes in list_yes:
		if yes in string:
			return 'U3'
	for no in list_no:
		if no in string:
			return 'U4'
	
	if string=='':	
		return 'U6'
	else:
		return 'U5'




# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
	
	req = request.get_json(silent=True, force=True)
	result = req.get("result")
	query = result.get("resolvedQuery")
	

	scope = ['https://www.googleapis.com/auth/drive']
	
	#ダウンロードしたjsonファイルを同じフォルダに格納して指定する
	credentials = ServiceAccountCredentials.from_json_keyfile_name('My First Project-fc3744a8d618.json', scope)
	gc = gspread.authorize(credentials)

	# # 共有設定したスプレッドシートの名前を指定する
	RespList = gc.open("FurikomeJudge").worksheet('RespList')
	Dialog = gc.open("FurikomeJudge").worksheet('Dialog')
	text = ""
	ID = ''
	UserResponse=''
	Talking=True
	IFTTT=False

	#行数を取得
	values_list = Dialog.col_values(1)
	num = 0
	for value in values_list:
		if value == '':
			break
		num+=1

	#もしシートに何の情報もなければ、T0として開始する
	#既に情報があるなら、その値を持ってくる
	if num == 2:
		ID = 'T0'
	else:
		ID = str(Dialog.cell(num,1).value)

	#User発話を書き込む
	Dialog.update_cell(num,3,query)

	#User発話から内容を判断する
	#中身はつくる
	if ID=='T0':
		UserResponse=T0_Judge(query)

	elif ID=='T1':
		UserResponse=T1_Judge(query)



	#判断されたIDは変数UserResponseに入れる
	#UserResponse、Next、Alertを探す。
	cell=RespList.find(UserResponse)
	Next=RespList.cell(cell.row,3).value
	Alert=RespList.cell(cell.row,4).value

	
	#返答の文言をtextに入れる
	num2=1
	cell_list=RespList.col_values(1)
	for value in cell_list:
		if value==Next:
			break
		num2=num2+1

	text=RespList.cell(num2,2).value

	#ここでyeildしてもいいかも。

	#ENDかどうか
	Next_Next=RespList.cell(num2,3).value
	if Next_Next=='END':
		Talking=False

	#Alertかどうか
	Alert_Arert=RespList.cell(num2,4).value
	if Alert_Arert=='TRUE':
		IFTTT=True

	#各変数をDialogに書き込む
	Dialog.update_cell(num,4,UserResponse)
	Dialog.update_cell(num,5,Next)
	Dialog.update_cell(num,6,Alert)
	Dialog.update_cell(num+1,1,Next)
	Dialog.update_cell(num+1,2,text)

	#もしENDなら、シートをクリーンアップする
	if Talking==False:
		Dialog.clear()
		Dialog.update_cell(1,1,'ID')
		Dialog.update_cell(1,2,'Request')
		Dialog.update_cell(1,3,'Query')
		Dialog.update_cell(1,4,'Judgement')
		Dialog.update_cell(1,5,'Next')
		Dialog.update_cell(1,6,'Alert')
		Dialog.update_cell(2,1,'T0')
		Dialog.update_cell(2,2,'誰からのお電話でしたか？')



	#json返す
	r = make_response(jsonify({'speech':text,'displayText':text,'data':{'google':{'expect_user_response':Talking,'no_input_prompts':[],'is_ssml':False}}}))
	r.headers['Content-Type'] = 'application/json'
	




	return r


if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	print("Starting app on port %d" % port)
	app.run(debug=False, port=port, host='0.0.0.0')

