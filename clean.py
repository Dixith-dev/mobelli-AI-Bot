import re

response = "Hey this is my response :- We were established in 2003【7†source】"

cleaned_response = re.sub(r'【.*】', '', response)

print(cleaned_response)