import randomGacha as gacha

userName = "admin"

def main():
    gacha_calculator = gacha.GachaCalculator(userName)
    # printAvableBanner(gacha_calculator)
    bannerName = "Rate-Up Mild-R"
    num_pulls = 1420
    item = gacha_calculator.multiple_pulls(bannerName, num_pulls)
    userDeatail = gacha_calculator.getUserDetail(userName, bannerName)
    print("เพชรคงเหลือ: ", gacha_calculator.get_user_gem(userName))

    print(f"BannerName: {userDeatail['BannerName']}\tGuaranteed: {userDeatail['IsGuaranteed']}\tNumberRoll: {userDeatail['NumberRoll']}\tเศษเกลือ: {userDeatail['Salt']}")

    count_tier = {"Count":0}
    count_SSR = {"Count":0}
    for i in range(len(item)):
        if item[i]["TierName"] == "SSR":
            if item[i]["Name"] not in count_SSR:
                count_SSR[item[i]["Name"]] = 0
            count_SSR[item[i]["Name"]] += 1
            count_SSR["Count"]+=1

        if item[i]["TierName"] not in count_tier:
            count_tier[item[i]["TierName"]] = 0
        count_tier[item[i]["TierName"]] += 1
        count_tier['Count'] += 1 

    print("num_pulls: ", num_pulls)
    print("R - SR: ")
    for key, value in count_tier.items():
        print(f"{key}: Rate: {100*value/count_tier['Count']:.2f}%, Count: {value}")
    print("\nSSR: ")
    for key, value in count_SSR.items():
        print(f"{key}: Rate: {100*value/count_SSR['Count']:.2f}%, Count: {value}")


def printAvableBanner(gacha_calculator):
    available_banners = gacha_calculator.getAvableBanner()
    for i in range(len(available_banners)):
        print("Banner Name: ", available_banners[i]["Name"])
        print("Start Date: ", available_banners[i]["start_date"])
        print("End Date: ", available_banners[i]["end_date"])
        print()
main()