import time
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import random, json
from seleniumwire.utils import decode

parsed_position_x = {}
parsed_position_x["Me gusta"]      = "Like Reaction Count"
parsed_position_x["Me encanta"]    = "Love Reaction Count"
parsed_position_x["Me divierte"]   = "Funny Reaction Count"
parsed_position_x["Me enfada"]     = "Angry Reaction Count"
parsed_position_x["Me asombra"]    = "Wow Reaction Count"
parsed_position_x["Me entristece"] = "Sad Reaction Count"

def get_reactions_count(data):
    reactions = data.get("data", {}).get("node", {}).get("top_reactions", {}).get("summary", [])
    parsed_reactions = {}
    for reaction in reactions:
        reaction_name = reaction.get("reaction", {}).get("localized_name", "no name")
        parsed_reactions[reaction_name] = reaction.get("reaction_count", 0)
    return parsed_reactions

df = pd.read_excel("./remain_posts.xlsx")

options = Options()
options.add_argument("user-data-dir=C:\\Users\\Cesar\\AppData\\Local\\Google\\Chrome\\User Data")
options.add_argument(r'--profile-directory=Default')
driver = webdriver.Chrome(executable_path=r'C:/Drivers/chromedriver.exe', options=options)#, desired_capabilities=capabilities)

invalid = []
for index, row in df.iterrows():
    if df.iloc[index]["has error"] == 1:
        post_url = df.iloc[index]["Post Url"]
        if post_url.count(":") == 1:
            try:
                driver.get(post_url)
                time.sleep(random.randint(3, 7))
                element = driver.find_element(By.XPATH, '//span[@role = "toolbar"]')
                del driver.requests
                element.click()
                time.sleep(random.randint(4, 6))
                found_request = False
                requests = driver.requests
                for request in requests:
                    if request.response:
                        if "graphql" in request.url:
                            print(request.response)
                            response_body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                            json_data = json.loads(response_body)
                            reactions = get_reactions_count(json_data)
                            print(f"url: {post_url} - {reactions}")
                            for reaction_name, reaction_count in reactions.items():
                                column_name = parsed_position_x.get(reaction_name)
                                if column_name is not None:
                                    df.at[index, column_name] = reaction_count
                            found_request = True
                if not found_request:
                    raise Exception("No request for the query") 
            except Exception as e:
                invalid.append({"url": post_url, "index df": index, "reason": str(e)})
                df.at[index, "has error"] = 1
                print({"url": post_url, "index df": index, "reason": str(e)})
        else:
            invalid.append({"url": post_url, "index df": index, "reason": "invalid url"})

        time.sleep(random.randint(2, 4))
driver.close()
df.to_excel("reactions.xlsx", index=False)
with open('invalid.json', 'w') as file:
    json.dump(invalid, file)