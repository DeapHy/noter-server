from flask import Flask, request
import psycopg2
from uuid import uuid4
from hashlib import md5
from datetime import datetime
from json import dumps

app = Flask(__name__)

# def log():
# 	print("yes")

def connectDB():
	conn = psycopg2.connect(
		dbname='d3ao19kgp0292q', 
		user='apxzyslyxttxja', 
 		password='cb589ba70270a10c5833cb2dab6e6cd09f5cd1858242715860a05d955b925f8e', 
 		host='ec2-52-215-225-178.eu-west-1.compute.amazonaws.com')
	cursor = conn.cursor()
	return [conn, cursor]

@app.route("/api/connect", methods=["POST"])
async def connect():
	try:
		[conn, cursor] = connectDB()
		return dumps({"success": True}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*"
		}
	except Exception as e:
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/index", methods=["GET"])
async def index():
	data = {
		"test": 123
	}
	return data, {
		"Content-Type": "application/json",
		"Access-Control-Allow-Origin": "*" 
	}

@app.route("/api/createAccount", methods=["POST"])
async def createAccount():
	body = request.json
	[conn, cursor] = connectDB()

	userid = uuid4()
	cursor.execute(f'SELECT * FROM public.users WHERE login=\'{body["login"]}\'')
	result = cursor.fetchall()
	if (len(result) > 0):
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

	salt = str(uuid4())
	hashedlogin = md5(f'{body["login"]}:{body["password"]}'.encode('utf-8')).hexdigest()
	hashh = md5(f"{salt}>>{hashedlogin}".encode('utf-8')).hexdigest()


	cursor.execute(f'INSERT INTO public.users(id, login, salt, hash) values (\'{userid}\', \'{body["login"]}\', \'{salt}\', \'{hashh}\')')
	cursor.execute(f'INSERT INTO public.userinfo(userid, name) VALUES (\'{userid}\', \'{body["login"]}\')')
	conn.commit()
	cursor.close()
	conn.close() 
	return dumps({"success": True}), {
		"Content-Type": "application/json",
		"Access-Control-Allow-Origin": "*" 
	}

@app.route("/api/getOneTimeToken", methods=["POST"])
async def getOTT():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT * FROM public.users WHERE login=\'{body["login"]}\'')
	result = cursor.fetchall()
	if (len(result) > 0):
		cursor.execute(f'SELECT * FROM public.users WHERE login=\'{body["login"]}\'')
		user = cursor.fetchall()
		cursor.close()
		conn.close()
		return dumps({"salt": user[0][2]}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}
	else:
		cursor.close()
		conn.close()
		return dumps({"salt": uuid4()}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/loginWithOneTimeToken", methods=["POST"])
async def loginWithOTT():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT * FROM public.users WHERE login=\'{body["login"]}\'')
	result = cursor.fetchall()[0]
	#print(result)
	if (result[1] == body["login"]) & (result[3] == body["hash"]):
		cursor.execute(f'INSERT INTO public.session(id, userid, opened) VALUES (\'{uuid4()}\', \'{result[0]}\', true)')

		cursor.execute(f'SELECT name FROM public.userinfo where userid=\'{result[0]}\'')
		result = cursor.fetchall()[0]
		nickname = result[0]

		conn.commit()
		cursor.close()
		conn.close()

		return dumps({"success": True, "nickname": nickname}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}	

@app.route("/api/setPseudonym", methods=["POST"])
async def setPseudo():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT id FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]
	
	cursor.execute(f'SELECT * FROM public.sessions WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):
		cursor.execute(f'SELECT * FROM public.userinfo WHERE userid=\'{userid}\'')
		result = cursor.fetchall()
		if (len(result) > 0):
			cursor.execute(f'UPDATE public.userinfo SET name=\'{body["nickname"]}\' where userid=\'{userid}\'')
		else:
			cursor.execute(f'INSERT INTO public.userinfo(userid, name) VALUES (\'{userid}\', \'{body["nickname"]}\')')
		conn.commit()
		cursor.close()
		conn.close()
		return dumps({"success": True}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/newNote", methods=["POST"])
async def newNote():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT id FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]

	cursor.execute(f'SELECT * FROM public.sessions WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):
		note = {
			"id": str(uuid4()),
			"title": body["note"]["title"],
			"content": body["note"]["content"],
			"date": f"{datetime.now().day}-{datetime.now().month}-{datetime.now().year}"
		}
		cursor.execute(f'INSERT INTO public.notes (id, userid, datetime, title, content) VALUES (\'{note["id"]}\', \'{userid}\', current_date, \'{note["title"]}\', \'{note["content"]}\')')
		conn.commit()
		cursor.close()
		conn.close()
		return dumps(
			{
				"success": True,
				"note": note
			}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
	else:
		cursor.close()
		conn.close()
		return dumps(
			{
				"success": False,
				"note": note
			}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}

@app.route("/api/getNotes", methods=["POST"])
async def getNotes():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT id FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]

	cursor.execute(f'SELECT * FROM public.session WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):

		cursor.execute(f'SELECT * FROM public.notes where userid=\'{userid}\'')
		result = cursor.fetchall()
		temp = []
		for i in range(len(result)):
			temp.append({
				"id": result[i][0],
				"userid": result[i][1],
				"date": f"{result[i][2].day}-{result[i][2].month}-{result[i][2].year}",
				"title": result[i][3],
				"content": result[i][4]
				})

		print(result)
		response = {"notes": temp}
		cursor.close()
		conn.close()
		return response, {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/updateNote", methods=["POST"])
async def updateNote():
	body = request.json
	[conn, cursor] = connectDB()

	# Проверка на открытость сессии
	cursor.execute(f'SELECT id FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]

	cursor.execute(f'SELECT * FROM public.session WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):

		cursor.execute(f'SELECT * FROM public.notes WHERE id=\'{body["id"]}\'')
		result = cursor.fetchall()
		if (len(result) > 0):
			cursor.execute(f'UPDATE public.notes SET title=\'{body["title"]}\', content=\'{body["content"]}\' WHERE id=\'{body["id"]}\'')
			conn.commit()
			cursor.close()
			conn.close()
			return dumps({"success": True}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
		else:
			cursor.close()
			conn.close()
			return dumps({"success": False}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/removeNote", methods=["POST"])
async def removeNote():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT id FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]

	cursor.execute(f'SELECT * FROM public.session WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):

		cursor.execute(f'SELECT * FROM public.notes WHERE id=\'{body["id"]}\'')
		result = cursor.fetchall()
		if (len(result) > 0):
			cursor.execute(f'DELETE FROM public.notes WHERE id=\'{body["id"]}\'')
			conn.commit()
			cursor.close()
			conn.close()
			return dumps({"success": True}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
		else:
			cursor.close()
			conn.close()
			return dumps({"success": False}), {
				"Content-Type": "application/json",
				"Access-Control-Allow-Origin": "*" 
			}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

@app.route("/api/logout", methods=["POST"])
async def logout():
	body = request.json
	[conn, cursor] = connectDB()

	cursor.execute(f'SELECT * FROM public.users WHERE login=\'{body["login"]}\'')
	userid = cursor.fetchall()[0][0]

	cursor.execute(f'SELECT * FROM public.session WHERE userid=\'{userid}\' and opened=true')
	result = cursor.fetchall()
	if (len(result) > 0):
		cursor.execute(f'UPDATE public.session SET opened=false WHERE userid=\'{userid}\'')
		conn.commit()
		cursor.close()
		conn.close()
		return dumps({"success": True}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}
	else:
		cursor.close()
		conn.close()
		return dumps({"success": False}), {
			"Content-Type": "application/json",
			"Access-Control-Allow-Origin": "*" 
		}

if __name__ == "__main__":
	app.run(host="192.168.0.118", port=5000, debug=True)
