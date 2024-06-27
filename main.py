import randomGacha as gacha

userName = "admin"

def main():
    gacha_calculator = gacha.GachaCalculator(userName)
    # printAvableBanner(gacha_calculator)
    bannerName = "Rate-Up Mild-R"
    
    item = gacha_calculator.multiple_pulls(bannerName, 10)
    userDeatail = gacha_calculator.getUserDetail(userName, bannerName)
    print("เพชรคงเหลือ: ", gacha_calculator.get_user_gem(userName))
    print(f"BannerName: {userDeatail['BannerName']}\tGuaranteed: {userDeatail['IsGuaranteed']}\tNumberRoll: {userDeatail['NumberRoll']}\tเศษเกลือ: {userDeatail['Salt']}")
    for i in range(len(item)):
        print("Name: %20s,\t Tier: %3s"%(item[i]["Name"], item[i]["TierName"]))

def printAvableBanner(gacha_calculator):
    available_banners = gacha_calculator.getAvableBanner()
    for i in range(len(available_banners)):
        print("Banner Name: ", available_banners[i]["Name"])
        print("Start Date: ", available_banners[i]["start_date"])
        print("End Date: ", available_banners[i]["end_date"])
        print()
main()