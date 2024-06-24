import numpy as np
import pandas as pd
from database.sqlquery import DatabaseManager


class GachaCalculator(DatabaseManager):
    def __init__(self, db_name: str, userName: str):
        super().__init__(db_name)

        self.GuaranteRate = 142
        self.gachaDiamondsUsed = 142
        self.gachaRate = super().get_rate_item()
        self.gachaItems = super().get_gacha_item()
        self.userName = userName
        self.thisUser = super().get_user_detail(userName)

    def getItemGacha(self, tier: str, bannerName: str):

        bannerTypeID = super().getBannerTypeID(bannerName)

        # ดึงข้อมูลขึ้นมา
        
        thisUser = self.thisUser[self.thisUser.BannerTypeID == bannerTypeID].iloc[0]
        thisUser["NumberRoll"] += 1

        # random
        # ถ้า NumberRoll ที่ GuaranteRate จะได้ UR
        # ถ้าไม่จะ สุ่ม R ถึง SSR
        if tier == "UR" or thisUser["NumberRoll"] > self.GuaranteRate:
            item, thisUser = self.getURItem(thisUser, bannerName)
        else:
            gachaItems = super().get_gacha_item(is_ur=False)

            gachaItems = gachaItems[gachaItems.TierName == tier]
            chosen_idx = np.random.choice(len(gachaItems), replace=True, size=1)
            data = gachaItems.iloc[chosen_idx].to_dict()

            ID = [*data["Name"]][0]
            # ตัวละครที่สุ่มได้ R-SSR
            item = {
                "Character_ID": ID,
                "Name": data["Name"][ID],
                "TierName": data["TierName"][ID],
                "Salt": data["Salt"][ID],
            }
        '''
        gacha user detail 
            จะเก็บว่า user นี้สุ่มตู้ ถาวร กับ Limited ไปแล้วเท่าไหร่ และตู้นั้นมีการันตีหรือไม่

        จะ Update NumberRoll และ การันตีว่าเป็น True หรือ False ตามตู้ที่สุ่ม
        '''

        super().update_user_detail(thisUser)
        
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
        # Get ตัวละครที่สามารถสุ่มได้ขึ้นมา ตามตู้ที่เลือกสุ่ม
        bannerItem = super().get_gacha_item(is_ur=True, bannerName=bannerName)

        # ดึง ประเภทของ Banner (Permanent กับ Limited)
        bannerTypes = super().list_banner_type()

        # Filter ประเภทของ ตัวละคร ตามตู้ที่เลือกสุ่ม
        BannerTypeID = bannerItem[bannerItem.BannerName == bannerName].BannerTypeID.iloc[0]

        # มีการันตีหรือไม่
        if thisUser.IsGuaranteed == True:
            # ได้ตามตู้ที่เลือกสุ่มแน่นอน
            thisUser.IsGuaranteed = 0
        else:
            # สุ่มได้ Permanent กับ Limited
            chosen_idx = np.random.choice(len(bannerTypes), replace=True, size=1)[0]
            banner = bannerTypes[chosen_idx]
            if banner["Name"] == "Permanent":
                thisUser.IsGuaranteed = 1
            else:  # สุ่มได้ Limited
                thisUser.IsGuaranteed = 0
            BannerTypeID = banner["ID"]

        # Reset NumberRoll
        thisUser.NumberRoll = 0
        bannerItem = bannerItem[bannerItem.BannerTypeID == BannerTypeID]
        chosen_idx = np.random.choice(len(bannerItem), replace=True, size=1)
        data = bannerItem.iloc[chosen_idx].to_dict()

        # assign ค่าลง user_log
        C_ID = [*data["Name"]][0]
        item = {
            "Character_ID": C_ID,
            "Name": data["Name"][C_ID],
            "TierName": data["TierName"][C_ID],
            "Salt": data["Salt"][C_ID],
        }
        return item, thisUser

    # สุ่ม 1 โล แต่Functionนี้ จะไม่ถูกใช้งานข้างนอก ให้ใช้ multiple_pulls(1) แทน
    def single_pull(self, bannerName: str):
        items = self.gachaRate
        item_list = list(items.keys())
        probabilities = list(items.values())
        tier = np.random.choice(item_list, size=1, replace=True, p=probabilities)[0]
        return self.getItemGacha(tier, bannerName)

    # Check Gem
    def checkGem(self, num_pulls:int):
        gem = super().getGemFromUser(self.userName)
        if gem < num_pulls*self.gachaDiamondsUsed:
            return False, 0
        remaining_diamonds = int(gem-(num_pulls*self.gachaDiamondsUsed))
        return True, remaining_diamonds
    
    def multiple_pulls(self, bannerName: str, num_pulls: int):
        # ดึงข้อมูล User จาก Database อีกรอบ
        self.thisUser = super().get_user_detail(self.userName)

        # Check ว่า Gem พอหรือไม่
        condition, gem = self.checkGem(num_pulls)
        if not condition:
            return {"Error": "Not Enough Gem"}
        print("เพชรคงเหลือ: ", gem)
        results = []
        user_log = pd.DataFrame(
            columns=["ID", "User_ID", "Character_ID", "Create_Date", "Banner_Type_ID"]
        )

        salt = 0
        # สุ่มกาชา
        for _ in range(num_pulls):
            item, df_new = self.single_pull(bannerName)

            # update user log
            if len(user_log) < 1:
                user_log = df_new
            else:
                user_log = pd.concat([user_log, df_new], ignore_index=True)
            salt += item["Salt"]
            results.append(item)
        userID = self.thisUser["UserID"].iloc[0]
        
        # update gem salt
        super().update_gem(gem, salt, userID)

        # assign UserID ลง user_log
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
            f"BannerName: {userDeatail.BannerName}\tGuaranteed: {userDeatail.IsGuaranteed}\tNumberRoll: {userDeatail.NumberRoll}\tเศษเกลือ: {userDeatail.Salt}"
        )
        return results


if __name__ == "__main__":
    # Connect to SQLite database
    pass
