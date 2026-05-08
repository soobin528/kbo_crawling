from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time


class GameCalCrawler:
    url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"

    def crawling(self, month):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(self.url)

            wait = WebDriverWait(driver, 10)

            # 월 선택 드롭다운 대기
            month_select = wait.until(
                EC.presence_of_element_located((By.ID, "ddlMonth"))
            )

            select = Select(month_select)
            select.select_by_value(month)

            # [추가] 월 드롭다운 변경 후 테이블 데이터가 바뀔 시간 확보
            time.sleep(1)

            # 월 변경 후 테이블 다시 로딩 대기
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tbl-type06")))

            table = driver.find_element(By.CLASS_NAME, "tbl-type06")
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")

            results = []
            current_date = None

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                values = [col.text.strip() for col in cols]

                if not values:
                    continue

                # 날짜가 있는 행
                if values[0].endswith(")"):
                    current_date = values[0]
                    values = values[1:]

                # 날짜가 없는 행
                if current_date is None:
                    continue

                # 최소 컬럼 확인
                if len(values) < 7:
                    continue

                time_text = values[0]
                game_text = values[1]
                game_center = values[2]
                highlight = values[3]
                tv = values[4]
                radio = values[5]
                stadium = values[6]
                note = values[7] if len(values) > 7 else "-"

                # 경기 일정만 저장
                results.append(
                    {
                        "date": current_date,
                        "time": time_text,
                        "game": game_text,
                        "stadium": stadium,
                        "note": note,
                    }
                )

            df = pd.DataFrame(results)

            os.makedirs("./app/game_schedule", exist_ok=True)

            # [추가] 월별 CSV 저장
            df.to_csv(
                f"./app/game_schedule/{month}m_schedule.csv",
                index=False,
                encoding="utf-8-sig",
            )

            df.to_json(
                f"./app/game_schedule/{month}m_schedule.json",
                force_ascii=False,
                orient="records",
                indent=4,
            )

            print(f"{month}월 경기 일정 저장 완료")
            print(df.head())

            return df

        finally:
            driver.quit()


if __name__ == "__main__":
    crawler = GameCalCrawler()
    all_df = []

    # [수정] 07월 한 번만 실행하던 것을 01~12월 전체 반복
    for month_num in range(1, 13):
        month = f"{month_num:02d}"
        df = crawler.crawling(month)
        all_df.append(df)

    # [추가] 12개월 데이터를 하나로 합치기
    total_df = pd.concat(all_df, ignore_index=True)

    # [추가] 2026 전체 파일로 저장
    total_df.to_csv(
        "./app/game_schedule/2026_kbo_schedule_all.csv",
        index=False,
        encoding="utf-8-sig",
    )

    total_df.to_json(
        "./app/game_schedule/2026_kbo_schedule_all.json",
        force_ascii=False,
        orient="records",
        indent=4,
    )

    print("2026 전체 경기 일정/결과 저장 완료")
    print("총 경기 수:", len(total_df))
