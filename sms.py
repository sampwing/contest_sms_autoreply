#!/usr/bin/env python
import time
import sqlite3
import re
import json
import random
import googlevoice as gv
import datetime

class Neg(object):


   call = None
   def __init__(self, filename):
      f = open(filename, "r")
      self.choices = [line.strip() for line in f]
      f.close()
      Neg.call = self

   def randomchoice(self):
      return random.choice(self.choices)


class QuestionHandler(object):
   def __init__(self, dbname):
      self.connection = sqlite3.connect(dbname)    
      self.cursor = self.connection.cursor()
      self.cursor.execute("SELECT MAX(Questions.qid) FROM Questions")
      level, = self.cursor.fetchone()      
      self.maxlevel = int(level)

   def getlevel(self, user):
      self.cursor.execute("SELECT Users.qid FROM Users WHERE Users.phone=?", (user,))
      currentlevel, = self.cursor.fetchone()
      return int(currentlevel)

   def getduration(self, user):
      self.cursor.execute("SELECT Users.created, Users.finished FROM Users WHERE Users.phone=?", (user,))
      created, finished, = self.cursor.fetchone()
      return finished-created

   def levelup(self, user):
      level = self.getlevel(user)
      print "Currently %d/%d level" % (level, self.maxlevel)
      if level >= self.maxlevel:
         return False # User is finished with the game
      else:
         self.cursor.execute("UPDATE Users SET qid=? WHERE phone=?", (str(level+1), user,))
         self.connection.commit()
         return True # User is the next level
         
   def checkanswer(self, user, message):
      question, answer = self.userinfo(user)
      print "user:", user
      print "sent:", message
      print "correct answer:", answer
      message_list = message.lower().split(' ')#re.findall(r"\w+", message)
      if len(set(answer.lower().split(' ')).intersection(set(message_list))) > 0:
         leveled = self.levelup(user)
         if leveled:
            if self.getlevel(user) == 1:
               return "You may now begin at Portal #1: Entrance. Happy testing!"
            question, answer = self.userinfo(user)
            if self.getlevel(user) == 2:
               return "Correct! You may now 'pass through' to Portal #1: Exit.\nHint: Use the Portal #1: Entrance image of the other side as a clue to finding Portal #1: Exit."
            else:
               return "Correct! You may now 'pass through' to Portal #%i: Exit." % self.getlevel(user)
         else:
            self.cursor.execute("UPDATE Users SET finished=? WHERE phone=?", (time.time(), user))
            self.connection.commit()
            duration = self.getduration(user)
            return "Congratulations! You have finished the game with a pitiful time of %s. Oh and we lied about the cake.\n\nYou will be contacted when the testing is complete." % (datetime.timedelta(seconds=duration))
      else:
         if self.getlevel(user) == 0: # game has not begun
            return "Text the word play to begin. You will find the first portal as well as directions in the BSOE hallway near Perk's."
         else: # wrong answer
            return "Sorry, %s is not the correct answer for this question.  Please try again at Portal #%s: Entrance." % (message, question)

   def createuser(self, user):
      self.cursor.execute("INSERT INTO Users(phone, qid, created) Values(?, 0, ?)", (user, time.time()))
      self.connection.commit()

   def userinfo(self, user):
      self.cursor.execute("SELECT Questions.question, Questions.answer FROM Questions, Users WHERE Questions.qid = Users.qid AND Users.phone=?", (user,))
      try:
         question, answer = self.cursor.fetchone()
         return question, answer
      except Exception, e:
         print e
         self.createuser(user)
         return self.userinfo(user)


class Spawn(object):


   def __init__(self, voice, db):
      self.voice = voice
      self.db = db

   def checkmessages(self):
      messages = self.voice.sms().messages
      for message in messages:
         if message.isRead == False:
            value = self.readmessage(message)
            print "check messages: ", value
            if value == True:
               message.mark()
               message.delete()
   
   def readmessage(self, message):
      user = message.phoneNumber
      text = message.messageText
      try:
         reply = self.db.checkanswer(user, text)
         self.voice.send_sms(user, reply)
         print "SENDING: %s\nTO:%s" % (reply, user)
         return True
      except Exception, e:
         print e
         return False


def main():
   Neg("neg_responses.data") # init Neg class
   voice = gv.Voice()
   username = "sampwing"
   password = "487-9783-8773-00"
   voice.login(email=username, passwd=password)
   db = QuestionHandler("portal.sqlite")
   spawn = Spawn(voice, db)
   while True:
      spawn.checkmessages()
      time.sleep(10)
   

if __name__ == '__main__':
   main()

