import requests
import requests.sessions
import sys
import re

Information = {'Author_Name':'Griffith Awuah',
               'Written on' : '19th January, 2017',
               'Description' : 'Library Used To Pull Links for all the lectures of a Udemy Course',
               'Health' : '99%',
               'Buggyness' : '*',
               'Dependencies' : [{'Requests': 'Kenneth Reitz',
                                  'Udemy-dl': 'Nishad'
                                  }
               ]
}

error_box = ['<li>You have exceeded the maximum number of requests per hour.</li>',
             '<li>Please check your email and password.</li>',
             'error',
             "Logout Wasn't Successful"
]

class Session:

    """Starting session with proper headers to access udemy site."""

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0',
               'X-Requested-With': 'XMLHttpRequest',
               'Host': 'www.udemy.com',
               'Referer': 'https://www.udemy.com/join/login-popup'}

    def __init__(self):
        """Init session."""
        self.session = requests.sessions.Session()

    def set_auth_headers(self, access_token, client_id):
        """Setting up authentication headers."""
        self.headers['X-Udemy-Bearer-Token'] = access_token
        self.headers['X-Udemy-Client-Id'] = client_id
        self.headers['Authorization'] = "Bearer " + access_token
        self.headers['X-Udemy-Authorization'] = "Bearer " + access_token

    def get(self, url):
        """Retrieving content of a given url."""
        return self.session.get(url, headers=self.headers)

    def post(self, url, data):
        """HTTP post given data with requests object."""
        return self.session.post(url, data, headers=self.headers)


session = Session()

def user_form() :
    username = input('Enter Your UserName or Email : ')
    password = input('Enter your Password : ')
    return (username, password)

def despace(course_name) :
    _x = course_name.split()
    return ''.join(word for word in _x)

def get_csrf_token():
    """Extractig CSRF Token from login page."""
    try:
        response = session.get('https://www.udemy.com/join/login-popup')
        match = re.search(r"name='csrfmiddlewaretoken'\s+value='(.*)'", response.text)
        return match.group(1)
    except AttributeError:
        session.get('http://www.udemy.com/user/logout')
        response = session.get('https://www.udemy.com/join/login-popup')
        match = re.search(r"name='csrfmiddlewaretoken'\s+value='(.*)'", response.text)
        return match.group(1)

def _write(filename, _data) :
    with open(filename + '.txt', 'w') as file :
        file.write(str(_data))

def login() :
    ''' Login To Udemy '''
    login_url = 'https://www.udemy.com/join/login-popup/?displayType=ajax&display_type=popup&showSkipButton=1&returnUrlAfterLogin=https%3A%2F%2Fwww.udemy.com%2F&next=https%3A%2F%2Fwww.udemy.com%2F&locale=en_US'
    csrf_token = get_csrf_token()
    username, password = user_form()
    payload = {'isSubmitted': 1, 'email': username, 'password': password,
               'displayType': 'ajax', 'csrfmiddlewaretoken': csrf_token}
    print('Attempting to Login to Udemy.com')
    response = session.post(login_url, payload) # Send a post using the wrapped request module

    access_token = response.cookies.get('access_token')
    client_id = response.cookies.get('client_id')
    response_text = response.text

    if error_box[0] in response_text:
        print('You have exceeded the maximum number of login requests per hour.')
        sys.exit(1)

    elif error_box[1] in response_text:
        print('Wrong Username or Password!')
        sys.exit(1)

    elif access_token is None:
        print("Couldn't fetch token!")
        sys.exit(1)

    elif error_box[2] in response_text:
        print(response_text)
        print('Found error in login page')
        sys.exit(1)

    session.set_auth_headers(access_token, client_id) #Authenticate Headers

    print("Login success.")

def get_course_id(course_link):
    """Retrieving course ID."""
    
    response = session.get(course_link)
    response_text = response.text

    if 'data-purpose="take-this-course-button"' in response_text:
        print('Please Enroll in this course')
        sys.exit(1)

    print('Searching course id...')
    matches = re.search(r'data-course-id="(\d+)"', response_text, re.IGNORECASE)
    if matches:
        course_id = matches.groups()[0]
    else:
        matches = re.search(r'property="og:image"\s+content="([^"]+)"', response_text, re.IGNORECASE)  # GIVE ATTENTION HERE. THERES A BUG SOMEHWERE HERE
        try :
            course_id = matches.groups()[0].rsplit('/', 1)[-1].split('_', 1)[0] 
        except :
            course_id = None

    if not course_id:
        print('Course id not found!')
        sys.exit(1)
    else:
        print('Found course id: %s', course_id)

    return course_id

def suck_endpoint(course_id) :
    """Getting data from endpoint"""
    course_url = 'https://www.udemy.com/api-2.0/courses/{0}/cached-subscriber-curriculum-items?fields[asset]=@min,title,filename,asset_type,external_url,length&fields[chapter]=@min,description,object_index,title,sort_order&fields[lecture]=@min,object_index,asset,supplementary_assets,sort_order,is_published,is_free&fields[quiz]=@min,object_index,title,sort_order,is_published&page_size=550'.format(str(course_id))
    course_data = session.get(course_url).json()
    _write('Course-Link', course_data)

def logout() :
    '''Logout From Udemy'''
    try :
        session.get('http://www.udemy.com/user/logout')
        return 'Logout Sucessful'
    except error : return error_box[3]

if __name__ == '__main__' :
    course = input('Enter Course-Name : ')
    course_name = despace(course)
    print(course_name)
    login()
    course_id = int(input('Enter Your Course ID :> '))
    suck_endpoint(course_id)
    print('done')
    print('logging out')
    logout()
    print('logged out successfully')
    
