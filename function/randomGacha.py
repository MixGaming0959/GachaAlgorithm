import os
import numpy as np
import pandas as pd
from database.sqlquery import DatabaseManager


class GachaCalculator(DatabaseManager):
    def __init__(self, db_name: str, userName: str):
        super().__init__(db_name)

        self.GuaranteRate = int(os.environ.get("GuaranteRate"))
        self.gachaDiamondsUsed = int(os.environ.get("gachaDiamondsUsed"))
        self.gachaRate = super().get_rate_item()
        self.gachaItems = super().get_gacha_item()
        self.userName = userName
        self.thisUser = super().get_user_detail(userName)

    def getItemGacha(self, tier: str, bannerName: str):
        # Get User Detail
        bannerTypeID = super().getBannerTypeID(bannerName)
        self.thisUser = super().get_user_detail(self.userName)
        thisUser = self.thisUser[self.thisUser.BannerTypeID == bannerTypeID].iloc[0]
        thisUser["NumberRoll"] += 1

        # random
        # ถ้า NumberRoll ที่ 90 จะได้ UR
        if tier == "UR" or thisUser["NumberRoll"] > self.GuaranteRate:
            item, thisUser = self.getURItem(thisUser, bannerName)
        else:
            gachaItems = super().get_gacha_item(is_ur=False)

            gachaItems = gachaItems[gachaItems.TierName == tier]
            chosen_idx = np.random.choice(len(gachaItems), replace=True, size=1)
            data = gachaItems.iloc[chosen_idx].to_dict()

            ID = [*data["Name"]][0]
            item = {
                "Character_ID": ID,
                "Name": data["Name"][ID],
                "TierName": data["TierName"][ID],
                "Salt": data["Salt"][ID],
            }

        super().update_user_detail(thisUser)
        
        # ["ID", "User_ID", "Character_ID", "Create_Date", "Banner_Type_ID"]
        data_log = {
            "ID": 0,
            "User_ID": thisUser["UserID"],
            "Character_ID": item["Character_ID"],
            "Create_Date": pd.Timestamp("now"),
            "Banner_Type_ID": bannerTypeID,
        }
        df_log = pd.DataFrame([data_log])
        return item, df_log

    def getURItem(self, thisUser, bannerName: str):
        bannerItem = super().get_gacha_item(is_ur=True, bannerName=bannerName)
        bannerTypes = super().list_banner_type()
        BannerTypeID = bannerItem[
            bannerItem.BannerName == bannerName
        ].BannerTypeID.iloc[0]
        if thisUser.IsGuaranteed == True:
            thisUser.IsGuaranteed = 0

        else:

            chosen_idx = np.random.choice(len(bannerTypes), replace=True, size=1)[0]
            banner = bannerTypes[chosen_idx]
            if banner["Name"] == "Permanent":
                thisUser.IsGuaranteed = 1
            else:  # Limited
                thisUser.IsGuaranteed = 0
            BannerTypeID = banner["ID"]

        thisUser.NumberRoll = 0
        bannerItem = bannerItem[bannerItem.BannerTypeID == BannerTypeID]
        chosen_idx = np.random.choice(len(bannerItem), replace=True, size=1)
        data = bannerItem.iloc[chosen_idx].to_dict()

        C_ID = [*data["Name"]][0]
        item = {
            "Character_ID": C_ID,
            "Name": data["Name"][C_ID],
            "TierName": data["TierName"][C_ID],
            "Salt": data["Salt"][C_ID],
        }
        return item, thisUser

    def single_pull(self, bannerName: str):
        items = self.gachaRate
        item_list = list(items.keys())
        probabilities = list(items.values())
        tier = np.random.choice(item_list, size=1, replace=True, p=probabilities)[0]
        return self.getItemGacha(tier, bannerName)

    def checkGem(self, num_pulls:int):
        gem = super().getGemFromUser(self.userName)
        if gem < num_pulls*self.gachaDiamondsUsed:
            return False, 0
        remaining_diamonds = int(gem-(num_pulls*self.gachaDiamondsUsed))
        return True, remaining_diamonds
    def multiple_pulls(self, bannerName: str, num_pulls: int):
        condition, gem = self.checkGem(num_pulls)
        if not condition:
            return {"Error": "Not Enough Gem"}
        print("เพชรคงเหลือ: ", gem)
        results = []
        user_log = pd.DataFrame(
            columns=["ID", "User_ID", "Character_ID", "Create_Date", "Banner_Type_ID"]
        )

        salt = 0
        for _ in range(num_pulls):
            item, df_new = self.single_pull(bannerName)
            if len(user_log) < 1:
                user_log = df_new
            else:
                user_log = pd.concat([user_log, df_new], ignore_index=True)
            salt += item["Salt"]
            results.append(item)
        userID = self.thisUser["UserID"].iloc[0]
        
        super().update_gem(gem, salt, userID)

        nextID = self.getNextID_UserLog()
        for index, _ in user_log.iterrows():
            user_log.loc[index, "ID"] = nextID
            nextID+=1
        super().insertUserGachaLog(user_log)
        userDeatail = self.getUserDetail(self.userName, bannerName).iloc[0]
        # print("BannerName\tGuaranteed\tNumberRoll")
        # print(
        #     f"{userDeatail.BannerName}\t{userDeatail.IsGuaranteed}\t\t{userDeatail.NumberRoll}"
        # )

        print(
            f"BannerName: {userDeatail.BannerName}\tGuaranteed: {userDeatail.IsGuaranteed}\tNumberRoll: {userDeatail.NumberRoll}"
        )
        return results


if __name__ == "__main__":
    # Connect to SQLite database
    pass
