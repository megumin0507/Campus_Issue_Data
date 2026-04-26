##### **1. issues**



The main object users browse.

issues

\- issue\_id

\- title

\- topic

\- description

\- cover\_summary

\- created\_at

\- updated\_at 



**Meaning**

* issue\_id: unique id for one campus issue
* title: the issue name shown on the page
* topic: category, like 宿舍, 社團, 課程開設, 成績辦法 (this should be a finite set defined by us and should not let AI generate it)
* description: short introduction of what this issue is
* cover\_summary: summary shown at the top of the page
* created\_at, updated\_at: system timestamps 







##### **2. events**



One concrete piece of information tied to an issue.

events

\- event\_id

\- issue\_id

\- source\_platform

\- source\_organization

\- source\_url

\- source\_authority

\- content\_type

\- content\_title

\- content\_content

\- content\_summary

\- time\_published\_at

\- time\_event\_at

\- topic

\- created\_at 



**Meaning**

* event\_id: unique id for one event
* issue\_id: which issue this event belongs to
* source\_platform: 學務處網站 / 學生會 IG
* source\_organization: 學務處 / 學生會 ...
* source\_url: original link
* source\_authority: 官方 / 半官方 / 非官方
* content\_type: 會議記錄 / 貼文
* content\_title: title of that piece of info
* content\_content: main extracted text
* content\_summary: short summary of this single event
* time\_published\_at: when the source was published
* time\_event\_at: when the actual event happened
* topic: classification
* created\_at: system timestamp 







##### **3. users** 



Just user.



users

\- user\_id

\- name

\- email

\- role

\- created\_at 



**Meaning**

* user\_id: unique id
* name: display name
* email: login/account identifier
* role: normal / admin / official
* created\_at: account creation time 







##### **4. comments**



Comments and replies can be merged into one table.

comments

\- comment\_id

\- issue\_id

\- user\_id

\- parent\_comment\_id

\- content

\- created\_at

\- updated\_at



**Meaning**

* comment\_id: unique id
* issue\_id: which issue this comment belongs to
* user\_id: who posted it
* parent\_comment\_id: null for normal comment, filled if it is a reply
* content: comment text
* created\_at, updated\_at: timestamps





