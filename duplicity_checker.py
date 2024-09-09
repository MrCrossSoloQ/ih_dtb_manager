class DuplicityChecker:
    def __init__(self, dtb_data, scraped_data):
        self.dtb_data = dtb_data
        self.scraped_data = scraped_data

    def dtb_duplicity_check(self):
        dtb_items = [dtb_item["elite_url"] for dtb_item in self.dtb_data]

        for scraped_data_item in self.scraped_data:
            if scraped_data_item.url not in dtb_items:
                print(f"V DTB se url adresa: {scraped_data_item.url} NENACHÁZÍ")
                return scraped_data_item
            else:
                print(f"V DTB se url adresa: {scraped_data_item.url} NACHÁZÍ")