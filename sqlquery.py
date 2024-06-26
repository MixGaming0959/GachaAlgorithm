from pandas import DataFrame, read_sql_query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name):
        self.engine = create_engine(f'sqlite:///{db_name}')
        self.Session = sessionmaker(bind=self.engine)

    def connect(self):
        return self.engine.connect()
    
    def getUserDetail(self, userName:str, bannerName:str):
        with self.engine.connect() as connection:
            query = f'''
            SELECT Banner.Name as BannerName, IsGuaranteed, NumberRoll, Salt FROM user_gacha_detail
                INNER JOIN User ON user_gacha_detail.User_ID = User.ID
                INNER JOIN Banner ON user_gacha_detail.Banner_Type_ID = Banner.Banner_Type_ID
            WHERE user.userName = '{userName}' AND Banner.Name = '{bannerName}';
            '''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query)
            return df
    
    # ดึง ID ของ UserLog ถัดไป
    def getNextID_UserLog(self):
        with self.engine.connect() as connection:
            query = f'''
            SELECT MAX(ID)+1 as ID FROM user_gacha_log;
            '''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query, columns=["ID"])
            nextID = 1
            if df["ID"].iloc[0] != None:
                nextID = int(df["ID"].iloc[0])
            return nextID

    # บันทึก UserLog
    def insertUserGachaLog(self, df_userLog):    
        with self.engine.connect() as connection:
            df_userLog.to_sql('user_gacha_log', connection, if_exists='append', index=False)

    # อัปเดต User Gacha Detail
    def update_user_detail(self, df_user):
        session = self.Session()
        timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            update_query = text(f'''
                UPDATE user_gacha_detail 
                SET IsGuaranteed = {df_user["IsGuaranteed"]}, NumberRoll = {df_user["NumberRoll"]} 
                , Updated_Date = '{timeNow}'
                WHERE User_ID = {df_user["UserID"]} AND Banner_Type_ID = {df_user["BannerTypeID"]};
            ''')
            session.execute(update_query)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating data: {e}")
        finally:
            session.close()

    #  ดึง BannerTypeID 
    def getBannerTypeID(self, bannerName:str):
        with self.engine.connect() as connection:
            
            query = f'''SELECT banner_type_id as BannerTypeID FROM banner WHERE Name = '{bannerName}' '''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query, columns=['BannerTypeID'])
            return int(df['BannerTypeID'].iloc[0])

    # ดึงข้อมูล User Gacha Detail
    def get_user_detail(self, userName:str):
        with self.engine.connect() as connection:
            query = f'''
            SELECT user.id as UserID, banner_type.ID as BannerTypeID, banner_type.Name as BannerType, IsGuaranteed, NumberRoll 
            FROM user_gacha_detail 
                INNER JOIN user ON user_gacha_detail.User_ID = user.id
                INNER JOIN banner_type ON user_gacha_detail.Banner_Type_ID = banner_type.id
            WHERE user.userName = '{userName}' '''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query)
            return df
    
    # ดึงข้อมูล ประเภทของBanner (Permanent กับ Limited)
    def list_banner_type(self):
        with self.engine.connect() as connection:
            query = f'''SELECT * FROM banner_type'''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query).to_dict(orient='records')
            return df

    # ดึง Rate Gacha
    def get_rate_item(self):
        with self.engine.connect() as connection:
            query = '''SELECT Name, Rate FROM character_tier'''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query).set_index('Name')
            total_probability = df['Rate'].sum()
            data = {}
            for index, _ in df.iterrows():
                df.loc[index, 'Rate'] /= total_probability
                data[index] = round(df.loc[index, 'Rate'], 5)
            return data
    
    # ดึง Gem จาก User
    def getGemFromUser(self, userName:str):
        with self.engine.connect() as connection:
            query = f'''SELECT Gem FROM user WHERE userName = '{userName}' '''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query, columns=['Gem'])
            return int(df['Gem'].iloc[0])

    # อัปเดต Gem    
    def update_gem(self, gem:int, salt:int, userID:int):
        session = self.Session()
        timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            sup_query = f'''
            (SELECT Salt FROM user WHERE ID = {userID})
            '''
            update_query = text(f'''
                UPDATE user SET Gem = {gem}, Salt = ({salt}+{sup_query}), Update_Date = '{timeNow}' WHERE ID = {userID};
            ''')
            session.execute(update_query)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating data: {e}")
        finally:
            session.close()

    # ดึงข้อมูล Banner ที่เปิดใช้งาน
    def getAvableBanner(self):
        with self.engine.connect() as connection:
            query = f'''SELECT Name, start_date, end_date FROM banner WHERE isEnable = 1'''
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query)
            return df.to_dict(orient='records')

    # ดึงข้อมูล Character ตามตู้ที่สุ่ม
    def get_gacha_item(self, is_ur:bool=False, bannerName:str='Permanent'):
        dic_bool = {
            True:1,
            False:0
        }
        where = ''
        if not is_ur:
            where = f'''WHERE ch.Is_UR = {dic_bool[is_ur]};'''
        else:
            item = ['Permanent']
            item.append(bannerName)
            item = [f'\'{i}\'' for i in item]
            where = f'''WHERE 
                ch.Is_UR = {dic_bool[is_ur]} AND 
                bru.Banner_ID in ( SELECT ID FROM banner WHERE Name in ({','.join(item)}));
            '''
        query = f'''
            SELECT ch.ID as Character_ID, ch.Name, tier.Name as TierName, 
                Banner.Name as BannerName, bt.ID as BannerTypeID, 
                bt.Name as BannerTypeName, tier.Salt, bru.Rate_Up as Rate_Up
            FROM `character` as ch
                INNER JOIN character_tier tier ON ch.Tier_ID = tier.id
                INNER JOIN banner_rate_up bru on bru.charcter_id = ch.id
                INNER JOIN Banner on Banner.ID = bru.Banner_ID
                INNER JOIN banner_type bt on bt.ID = Banner.banner_type_id 
            {where}
            '''
        with self.engine.connect() as connection:
            
            sql_query = read_sql_query(query, connection)
            df = DataFrame(sql_query).set_index('Character_ID')
            df['Rate_Up'] = df['Rate_Up'].astype(float)
            return df


if __name__ == "__main__":
    # Connect to SQLite database
    db_name = "database.db"
    db_manager = DatabaseManager(db_name)
    userName = "admin"

    # Get rate items
    item = db_manager.getGemFromUser(userName)
    print(item)
    
    # # Get gacha items
    # gacha_items = db_manager.get_gacha_item()
    # print(gacha_items)