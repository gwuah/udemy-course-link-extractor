import requests
import requests.sessions
import sys
import re


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
    return '-'.join(word for word in _x)

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

def write_to_file(filename, _data) :
    with open(filename + '.txt', 'w') as file :
        for url in _data :
            file.write(str(url) + "\n")
            
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

def get_course_id(courseName):
    """Retrieving course ID."""
    course_link = "https://www.udemy.com/{}/learn/v4/overview".format(courseName)
    response = session.get(course_link)
    markup = response.text

    if 'data-purpose="take-this-course-button"' in markup:
        print('Please Enroll in this course')
        sys.exit(1)

    print('Searching for course id...')
    match = re.search(r'property="og:image"\s+content="([^"]+)"', markup, re.IGNORECASE).groups()[0]
    print(match)
    courseId = re.search(r'(\d+)_', match).groups()[0]
    print('Found course id: %s', courseId)
    return int(courseId)

def suck_endpoint(courseId) :
    """Getting data from endpoint"""
    course_url = 'https://www.udemy.com/api-2.0/courses/{0}/cached-subscriber-curriculum-items?fields[asset]=@min,title,filename,asset_type,external_url,length&fields[chapter]=@min,description,object_index,title,sort_order&fields[lecture]=@min,object_index,asset,supplementary_assets,sort_order,is_published,is_free&fields[quiz]=@min,object_index,title,sort_order,is_published&page_size=550'.format(str(courseId))
    data = session.get(course_url).json()
    course_data = parser(data["results"])
    write_to_file('Udemy [{}]'.format(courseName), course_data)

def logout() :
    '''Logout From Udemy'''
    try :
        session.get('http://www.udemy.com/user/logout')
        return 'Logout Sucessful'
    except error : return error_box[3]
    
def buildObject(obj) :
    if ("asset" in obj) and (obj["asset"]["asset_type"] == "Video") : 
        dl = "https://www.udemy.com/{}/learn/v4/t/lecture/{}?start=0".format(courseName, obj['id'])
        return dl
    
def is_not_undefined(x):
    return x != None

    
def parser(api) :
    links = list(map(buildObject,api))
    data = list(filter(is_not_undefined, links))
    return data

if __name__ == '__main__' :
    course = input('Enter Course-Name : ')
    courseName = despace(course)
    print(courseName)
    login()
    course_id = get_course_id(courseName)
    suck_endpoint(course_id)
    print('Links Collected')
    print('Logging Out')
    logout()
    print('Logged Out Successfully')
    
