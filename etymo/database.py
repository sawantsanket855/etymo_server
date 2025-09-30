from django.db import connection
from django.core.mail import EmailMultiAlternatives
import random
from datetime import datetime, timezone
import secrets
from psycopg2 import Binary

def login(email,password):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT);
                           select * from tbl_login_data where col_email = '{email}' and col_password = '{password}';""")
            rows=cursor.fetchall()
            if rows:
                return 'correct credentials'
            else:
                return 'invalid credentials'
    
    except Exception as e:
        print(e)
        return 'server error'
    
def register(username,email,password):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT);
                           insert into tbl_login_data (col_username,col_email,col_password) values('{username}','{email}','{password}');""")
            rows=cursor.rowcount
            print(rows)
            return 'registered'
            
    except Exception as e:
        return 'email already exist'


def generate_otp():
    otp=random.randint(1000,9999)
    return otp

def sendOTP(email):
    otp=generate_otp()

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                            select * from tbl_login_data where col_email = '{email}' 
                            """)
            rows=cursor.rowcount
            if(rows):
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS tbl_otp(
                               col_email_id TEXT,
                               col_otp INT,
                               col_gen_time TIMESTAMPTZ DEFAULT NOW(),
                               col_isused BOOLEAN DEFAULT FALSE);
                               insert into tbl_otp(col_email_id,col_otp) values('{email}','{otp}');''')
            else:
                return 'email not registerd'
    except Exception as e:
        return 'error'
    
    try:
        print('start otp sending')
        subject = "Welcome to GST Web Portal !"
        from_email = "sanketsawant4123@gmail.com"
        to = [email]
        text_content = "OTP."
        html_content = f"<p><b>{otp}</b> This is your otp for login. Please don't share it with others</p>"

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        return 'error'
    return "otp sent"


def verifyOTP(email,otp):
    if not otp.isnumeric():
        return 'incorrect otp'
    try:
        with connection.cursor() as cursor:
            # cursor.execute(f"select * from tbl_otp where col_email_id='{email}' AND col_gen_time > NOW() - INTERVAL '5 minutes' ORDER BY col_gen_time DESC LIMIT 5")
            cursor.execute(f"select * from tbl_otp where col_email_id='{email}' ORDER BY col_gen_time DESC LIMIT 1")
            rows=cursor.fetchall()
            if(rows):
                data=rows[0]
                diff=datetime.now(timezone.utc)-data[2]
                if(diff.total_seconds()<300 and not data[3]):
                    print('otp gen',data[1])
                    if(data[1]==int(otp)):
                        print('correct otp')
                        try:
                            cursor.execute(f"update tbl_otp SET col_isused = True WHERE col_email_id ='{email}' AND col_otp='{data[1]}';")
                            print('otp status updated')
                        except Exception as e:
                            print(e)
                            return 'server error'
                    else:
                        return 'incorrect otp'
                else:
                    return 'otp expired'
            else:
                return 'otp not sent'
            return 'correct otp'
    except Exception as e:
        print(e)
        return 'error'
    
def sendPasswordResetEmail(email):
    username=None    
    reset_token=createResetPasswordToken(email)
    # reset_link=f"https://effulgent-torte-d90e0a.netlify.app/resetpassword/{email}/{reset_token}/"
    reset_link=f"http://localhost:3000/resetpassword/{email}/{reset_token}/"
    try:
        with connection.cursor() as cursor:
            print(email)
            cursor.execute(f"""
                           create table IF NOT EXISTS tbl_login_data(col_username TEXT,col_email TEXT UNIQUE,col_password TEXT);
                           select col_username from tbl_login_data where col_email ='{email}'""")
            rows=cursor.fetchall()
            username=rows[0][0]
            print(f'username is {username}')
        subject = "Reset Password"
        from_email="sanketsawant4123@gmail.com"
        to=[email]
        text_content='Reset Password'
        html_content= f"<p>Hello {username},<br> We received a request to reset your password for your GST webportal account.<br>Click the link below to set a new password: <br><a href='{reset_link}'>reset_link</a><br>This link will expire in 15 minutes. If you did not request a password reset, you can safely ignore this email.</p>"
        msg= EmailMultiAlternatives(subject,text_content,from_email,to)
        msg.attach_alternative(html_content,"text/html")
        msg.send()
        return 'reset password email sent'
    except Exception as e:
         print(e)
         return 'server error'

def createResetPasswordToken(email):
    reset_token=secrets.token_urlsafe(32)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS tbl_reset_token(
                               col_email_id TEXT,
                               col_reset_token TEXT,
                               col_gen_time TIMESTAMPTZ DEFAULT NOW(),
                               col_isused BOOLEAN DEFAULT FALSE);
                               insert into tbl_reset_token(col_email_id,col_reset_token) values('{email}','{reset_token}');''') 
            return reset_token

    except Exception as e:
        print(f'error: {e}')
        return 0
    
def updatePassword(email,reset_token,password):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT col_email_id FROM tbl_reset_token where col_email_id='{email}' and col_reset_token='{reset_token}' and col_gen_time > NOW() - INTERVAL '15 minutes' and col_isused=False;")
            rows=cursor.fetchall()
            if rows:
                cursor.execute(f'''update tbl_login_data set col_password='{password}' where col_email='{email}';
                                   update tbl_reset_token set col_isused = TRUE where col_email_id='{email}' and col_reset_token='{reset_token}'
                               ''')
                return 'password changed'
            else:
                return 'token expired'
    except Exception as e:
        print(e)
        return 'error'

        
def submit_request(name,type_,email,mobile,description,documents,):
    try:
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS tbl_request(col_id SERIAL PRIMARY KEY, col_name TEXT,col_type TEXT ,col_email TEXT,col_mobile TEXT,col_description TEXT,col_status TEXT default 'Under Review',col_instruction TEXT DEFAULT '' ,col_created_at TIMESTAMPTZ default NOW());
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_request (col_name,col_type,col_email,col_mobile,col_description)  VALUES (%s, %s, %s, %s, %s) RETURNING col_id;
                            """,(name, type_, email, mobile, description) )
            new_id = cursor.fetchone()[0]
            print(new_id)

            for doc in documents:
                byte_data=doc.read()
                print("Name:",doc.name ) 
                print("Type:", doc.content_type)
                print("Size:", len(byte_data))
            
                cursor.execute(f"""
                                CREATE TABLE IF NOT EXISTS tbl_documents (
                                                        col_id SERIAL PRIMARY KEY,
                                                        col_request_id INT REFERENCES tbl_request(col_id) ON DELETE CASCADE, -- link to request
                                                        col_filename TEXT,
                                                        col_content_type TEXT,
                                                        col_file_data BYTEA,
                                                        col_created_at TIMESTAMPTZ DEFAULT NOW()
                                                    );
                               INSERT INTO tbl_documents (col_request_id,col_filename,col_content_type,col_file_data)  VALUES (%s, %s, %s, %s);
                                """,(new_id,doc.name,doc.content_type,byte_data))
            
            print('submitted')
            return 'submitted'
    except Exception as e:
        print(e)
        return 'server error'


def get_request_document(request_id):
    try:
        with connection.cursor() as cursor:
            # cursor.execute("""
            #         select col_id from tbl_request order by col_created_at DESC
            #     """)
            # request_id=cursor.fetchone()[0]
            # print(request_id)
            cursor.execute(f"""
                    select col_id ,col_filename, col_content_type from tbl_documents where col_request_id={request_id}
                """)
            data=cursor.fetchall()
            print(data)
            return data
    except Exception as e:
        print(e)

    

def get_request_data():
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    select * from tbl_request order by col_created_at DESC
                """)
            data=cursor.fetchall()
            print(data)
            return data
    except Exception as e:
        print(e)
        return tuple()




def get_request_document_data(id):
    try:
        print('get_request_document_data')
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select col_content_type,col_file_data from tbl_documents where col_id={id}
                """)
            data= cursor.fetchone()
            print(data)
            return data
    except Exception as e:
        print(e)



def ca_cs_registartion(data):
    try:
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS tbl_ca_cs(col_id SERIAL PRIMARY KEY, col_name TEXT,col_role TEXT, col_specialization TEXT ,col_email TEXT,col_mobile TEXT,col_regNumber TEXT,col_workingDays TEXT[], col_created_at TIMESTAMPTZ default NOW());
                            """)
            cursor.execute(f"""
                           INSERT INTO tbl_ca_cs (col_name,col_role,col_specialization, col_email,col_mobile,col_regNumber,col_workingDays) VALUES (%s, %s, %s, %s, %s ,%s, %s) RETURNING col_id;
                            """,(data['name'],data['role'],data['specialization'], data['email'], data['mobile'], data['regNumber'],['mon','tue','wed']) )
            new_id = cursor.fetchone()[0]
            print(new_id)

            # for doc in documents:
            #     byte_data=doc.read()
            #     print("Name:",doc.name ) 
            #     print("Type:", doc.content_type)
            #     print("Size:", len(byte_data))
            
            #     cursor.execute(f"""
            #                     CREATE TABLE IF NOT EXISTS tbl_documents (
            #                                             col_id SERIAL PRIMARY KEY,
            #                                             col_request_id INT REFERENCES tbl_request(col_id) ON DELETE CASCADE, -- link to request
            #                                             col_filename TEXT,
            #                                             col_content_type TEXT,
            #                                             col_file_data BYTEA,
            #                                             col_created_at TIMESTAMPTZ DEFAULT NOW()
            #                                         );
            #                    INSERT INTO tbl_documents (col_request_id,col_filename,col_content_type,col_file_data)  VALUES (%s, %s, %s, %s);
            #                     """,(new_id,doc.name,doc.content_type,byte_data))
            
            print('submitted')
            return 'submitted'
    except Exception as e:
        print(e)
        return 'server error'




def update_request_status(requestId,requestStatus,requestInstruction):
    try:
        print('in update_request_status')
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                    UPDATE tbl_request SET col_status= %s, col_instruction = %s where col_id = %s RETURNING col_status;
                 """ ,(requestStatus,requestInstruction,requestId)  
            )
            new_status=cursor.fetchone()[0]
            print(f'updated status : {new_status}')

    except Exception as e:
        print(e)
        return 'server error'
