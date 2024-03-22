__author__ = ["Nick Riccobono"]
__copyright__ = "Copyright 2024, National Renewable Energy Laboratory"
__maintainer__ = "Nick Riccobono"
__email__ = ["nicholas.riccobono@nrel.gov"]


import requests
import json
import prettytable

DEFAULT_IDS = {"iron_steel": "WPU101",

              }

START_YEAR = "2014"
END_YEAR = "2024"

class BlsWebApi:

    def __init__(self, **kwargs):
        """
        Creates an instance of BlsWebApi

        Parameters
        ----------

        """
        self.series_dict = kwargs.get("series_ids", DEFAULT_IDS)
        self.start_year = kwargs.get("start_year", START_YEAR)
        self.end_year   = kwargs.get("end_year", END_YEAR)

        self.headers = {"Content-type": "application/json"}

        self.url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'

        print("Start-End years: ", self.start_year, " - ", self.end_year)

    def run_api(self, **kwargs):

        self.get_series_ids()

        #
        self.json_data = self.get_json_data()

        for series in self.json_data['Results']['series']:
            x=prettytable.PrettyTable(["series id","year","period","value","footnotes"])
            seriesId = series['seriesID']

        for item in series['data']:
            year = item['year']
            period = item['period']
            value = item['value']
            footnotes=""
            for footnote in item['footnotes']:
                if footnote:
                    footnotes = footnotes + footnote['text'] + ','
            if 'M01' <= period <= 'M12':
                x.add_row([seriesId,year,period,value,footnotes[0:-1]])

            output = open(seriesId + '.txt','w')
            output.write (x.get_string())
            output.close()

    def get_series_ids(self):
        """
        process series dictionary to get items (names) and values (ids)
        """

        series_names_list = []
        series_ids_list = []

        for k,v in self.series_dict.items():

            series_names_list.append(k)
            series_ids_list.append(v)

        print(series_names_list)
        print(series_ids_list)

        self.series_names = series_names_list
        self.series_ids = series_ids_list

    def get_json_data(self):

        #headers = {'Content-type': 'application/json'}

        data = json.dumps({"seriesid": self.series_ids,
                           "startyear": self.start_year,
                           "endyear": self.end_year}
        )
        p = requests.post(self.url,
                          data=data,
                          headers=self.headers
        )

        return json.loads(p.text)


if __name__ == "__main__":

    B = BlsWebApi()
    B.run_api()