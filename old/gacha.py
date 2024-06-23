import random
import json
import os

def load_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def update_User(data):
    # Up
    with open('database_user.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        
rate_Items = load_file("database_rate.json")
gacha_Items = load_file("database_Gacha.json")

# Normalize probabilities (in case they don't sum up to 1)
total_probability = sum(rate_Items.values())
for item in rate_Items:
    rate_Items[item] /= total_probability

def getItemGacha(tier, userName, bannerName):
    
    userData = load_file("database_user.json")#[userName][bannerName]
    thisUser = userData[userName][bannerName]
    thisUser["NumberRoll"] += 1

    # random
    # ถ้า NumberRoll ที่ 90 จะได้ UR
    if tier == "Ultra Rare Item" or thisUser["NumberRoll"] > 90:
        item, thisUser  = getURItem(thisUser, bannerName)
    else:
        item = random.choice(gacha_Items[tier])
    # print("Gacaha: ", item)

    # update Roll
    userData[userName][bannerName] = thisUser
    update_User(userData)
    # Ramdom Common - Super rare
    
    return item

def getURItem(userData, bannerName):
    bannerNameTMP = bannerName.copy()
    bannerItem = load_file("database_banner.json")
    if userData["IsGuaranteed"]:
        # update garanteed -> false
        # Reset Roll
        userData["IsGuaranteed"] = False
        userData["NumberRoll"] = 0
        
        
    else:
        random_Banner = random.choice(bannerItem.keys())
        # update garanteed -> true
        userData["IsGuaranteed"] = True
        userData["NumberRoll"] = 0
        item = random.choice(bannerItem["Banner_Permanent"])

    
    item = random.choice(bannerItem[bannerName])
    return item, userData

# Step 2: Function to simulate a single pull
def single_pull(items, userName, bannerName):
    item_list = list(items.keys())
    probabilities = list(items.values())
    tier = random.choices(item_list, probabilities)[0]
    return getItemGacha(tier, userName, bannerName)

# Step 3: Function to simulate multiple pulls
def multiple_pulls(items, num_pulls, userName, bannerName):
    results = []
    for _ in range(num_pulls):
        item = single_pull(items, userName, bannerName)
        results.append(item)
    return results

# Input UserName
userName = "Tester"

# เลือก Banner
bannerName = "World_End"
# Banner_Permanent, World_End

print("Banner: ", bannerName)
# Example usage
num_pulls = 10
# print(single_pull(rate_Items, userName, bannerName))
results = multiple_pulls(rate_Items, num_pulls, userName, bannerName)

# Display the results

for i in range(num_pulls):
    print(i+1, results[i])