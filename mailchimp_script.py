"""
Script to Extract the data from MailChimp 
and update that record in Knack Database.
"""
import pprint, json, requests, os, logging, datetime, argparse
from dotenv import load_dotenv
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
import dateutil.parser as dparser

pp = pprint.PrettyPrinter(indent=4)
load_dotenv()


class MailchimpScripts:
    """
    getting records from mailchimp and update in knack's database
    """

    def __init__(self, mailchimp_list_id):
        self.MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
        self.MAILCHIMP_SERVER = os.getenv("MAILCHIMP_SERVER")
        self.KNACK_APP_ID = os.getenv("KNACK_APP_ID")
        self.KNACK_KEY = os.getenv("KNACK_KEY")
        self.id_ = mailchimp_list_id

        self.client = MailchimpMarketing.Client()
        self.client.set_config(
            {"api_key": self.MAILCHIMP_API_KEY, "server": self.MAILCHIMP_SERVER}
        )

        self.date_ = datetime.datetime.now().date()
        # script logging
        filename = os.path.join(os.getcwd(), f"logs/{self.id_}_{self.date_}_logs.log")
        logging.basicConfig(
            filename=filename, format="%(asctime)s %(message)s", filemode="a"
        )
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    def get_all_lists(self):
        """
        get_all_lists
        Get information about all lists in the account
        returns: lists of members in a Mailchimp list
        """
        list_ids = list()
        lists_response = self.client.lists.get_all_lists()
        for list_ in lists_response.get("lists"):
            list_ids.append(list_["id"])

        return list_ids

    def get_list_member_info(self, list_ids=None):
        """
        get_list_member_info
        Get information about members in a specific Mailchimp list
        :param list_ids: lists of members in a Mailchimp list
        """
        self.logger.info("get_list_member_info() :: started")
        count_set = 0

        list_info_response = self.client.lists.get_list_members_info(
            self.id_, count=1000, offset=count_set
        )
        range_ = int(int(list_info_response.get("total_items")) / 1000)

        for i in range(0, range_ + 1):
            list_info_response = self.client.lists.get_list_members_info(
                self.id_, count=1000, offset=count_set
            )
            count_set += 1000

            if not list_info_response.get("members"):
                self.logger.info("get_list_member_info() :: [list members not found]")
                print("get_list_member_info() :: [list members not found]")
                break
            else:
                for members_ in list_info_response.get("members"):
                    if members_.get("status") == "subscribed":
                        continue

                    if members_.get("merge_fields").get("KNACKDATE") is None:
                        self.get_knack_record(members_)

                    elif members_.get("merge_fields").get("KNACKDATE") < str(
                        dparser.parse(members_.get("last_changed"), fuzzy=True).date()
                    ):
                        self.get_knack_record(members_)

                    #
                    # signal record testing, just for testing
                    #
                    """
                    if (
                        members_.get("email_address") == "maggierazzi@icloud.com"
                    ):
                        if members_.get("merge_fields").get("KNACKDATE") is None:
                            self.get_knack_record(members_)
                        elif members_.get("merge_fields").get("KNACKDATE") < str(dparser.parse(members_.get("last_changed"),fuzzy=True).date()):
                            self.get_knack_record(members_)
                    """

    def get_knack_record(self, members_info):
        """
        get_knack_record
        Get information in Knack databases corresponding to Mailchimp members
        and update the status in Knack databases corresponding to Mailchimp members
        :param members_info: mailchimp members information
        """
        print("get_knack_one_record() started.....")
        tb_object = "object_14"
        email_ID = members_info.get("email_address")
        headers = {
            "X-Knack-Application-Id": self.KNACK_APP_ID,
            "X-Knack-REST-API-Key": self.KNACK_KEY,
        }
        filter_set = json.dumps(
            {
                "match": "and",
                "rules": [
                    {"field": "field_64", "operator": "is", "value": f"{email_ID}"}
                ],
            }
        )
        try:
            url = f"https://api.knack.com/v1/objects/{tb_object}/records/?filters={filter_set}"
            response = requests.request("GET", url, headers=headers)
        except Exception as e:
            print("[get_knack_one_record()] :: [error] ::", e)
            return False

        knack_data = json.loads(response.text)
        if response.status_code == 429:
            self.logger.info(
                f"get_knack_one_record() :: [{email_ID}] :: [Error] :: [{response.text}]"
            )
            print(
                f"get_knack_one_record() :: [{email_ID}] :: [Error] :: [{response.text}]"
            )

        if not knack_data.get("records"):
            self.logger.info(
                f"get_knack_one_record() :: [Record not found in Knack DB corresponding to '{email_ID}' account]"
            )
            print(
                f"get_knack_one_record() :: [Record not found in Knack DB corresponding to '{email_ID}' account]"
            )
            return True

        knack_record_id = knack_data.get("records")[0].get("id")

        if members_info.get("status") == "cleaned":
            self.update_knack_record(
                tb_object,
                knack_record_id,
                members_info,
                members_info.get("status"),
                members_info.get("last_changed"),
                cleaned=members_info.get("last_changed"),
            )
        if members_info.get("status") == "unsubscribed":
            self.update_knack_record(
                tb_object,
                knack_record_id,
                members_info,
                members_info.get("status"),
                members_info.get("last_changed"),
                unsub=members_info.get("last_changed"),
            )
        print("Task has Done!")
        # return

    def update_knack_record(
        self,
        tb_object,
        id,
        members_info,
        Status=None,
        Update=None,
        cleaned=None,
        unsub=None,
    ):
        """
        update_knack_record
        Get all information from get_knack_record and update the status accordingly
        :param tb_object: Name of table object
        :param id: Id of members in knack database
        :param members_info: information of Mailchimp member
        :param status: the status which is update in Knack records
        :param update: the update datetime of Mailchimp member which need to update in Knack Database
        :param cleaned: cleaned datetimme which need to update in Knack Database
        :param unsub: unsub datetime which need to update in Knack Database
        """

        print("update_knack_record() started")
        url = f"https://api.knack.com/v1/objects/{tb_object}/records/{id}"

        headers = {
            "X-Knack-Application-Id": self.KNACK_APP_ID,
            "X-Knack-REST-API-Key": self.KNACK_KEY,
            "Content-Type": "application/json",
        }

        payload = None

        if members_info.get("list_id") == "31a1719578":
            payload = self.Health_Imaging(
                Status=Status, Update=Update, cleaned=cleaned, unsub=unsub
            )
        if members_info.get("list_id") == "342e16db33":
            payload = self.Radiology_Business(
                Status=Status, Update=Update, cleaned=cleaned, unsub=unsub
            )
        if members_info.get("list_id") == "8725f4d734":
            payload = self.Cardiovascular_Business(
                Status=Status, Update=Update, cleaned=cleaned, unsub=unsub
            )
        if members_info.get("list_id") == "afd9a8e4ef":
            payload = self.Health_Exec(
                Status=Status, Update=Update, cleaned=cleaned, unsub=unsub
            )
        if members_info.get("list_id") == "fdc72b3ec4":
            payload = self.AI_Healthcare(
                Status=Status, Update=Update, cleaned=cleaned, unsub=unsub
            )

        try:
            email_address = members_info.get("email_address")
            self.logger.info(
                f"update_knack_record() :: [members_info of {email_address} account is processing]"
            )
            print(
                f"update_knack_record() :: [members_info of {email_address} account is processing]"
            )
            response = requests.request("PUT", url, headers=headers, data=payload)
            if response.status_code == 200:
                self.update_list_member(members_info)
                self.logger.info(
                    f"update_knack_record() :: [members_info of {email_address} account has been updated]"
                )
                print(
                    f"update_knack_record() :: [members_info of {email_address} account has been updated]"
                )

                print(
                    email_address,
                    file=open(f"processed_email/{self.id_}_{self.date_}_email.txt", "a"),
                )
            else:
                self.logger.error(
                    f"update_knack_record() :: [account {email_address}] :: [status_code {response.status_code}] :: [message {response.text}]"
                )
                print(
                    f"update_knack_record() :: [account {email_address}] :: [status_code {response.status_code}] :: [message {response.text}]"
                )
        except Exception as e:
            print("update_knack_record() :: [error] :: ", e)
            self.logger.error("update_knack_record() :: [error] :: ", e)

    def Health_Imaging(self, Status, Update, cleaned=None, unsub=None):
        """
        HI_Status = 'field_247'
        HI_Update = 'field_299'
        HI_cleaned = 'field_260'
        HI_unsub = 'field_256'
        """
        health_imaging = {"field_247": Status, "field_299": Update}
        if cleaned is not None:
            health_imaging["field_260"] = cleaned

        if unsub is not None:
            health_imaging["field_256"] = unsub
        return json.dumps(health_imaging)

    def Radiology_Business(self, Status, Update, cleaned=None, unsub=None):
        """
        RB_Status = 'field_249'
        RB_Update = 'field_300'
        RB_cleaned = 'field_261'
        RB_unsub = 'field_257'
        """
        radiology_business = {"field_249": Status, "field_300": Update}

        if cleaned is not None:
            radiology_business["field_261"] = cleaned

        if unsub is not None:
            radiology_business["field_257"] = unsub

        return json.dumps(radiology_business)

    def Cardiovascular_Business(self, Status, Update, cleaned=None, unsub=None):
        """
        CVB_Status = 'field_246'
        CVB_Update = 'field_298'
        CVB_cleaned = 'field_259'
        CVB_unsub = 'field_255'
        """
        cardiovascular_business = {
            "field_246": Status,
            "field_298": Update,
        }

        if cleaned is not None:
            cardiovascular_business["field_259"] = cleaned

        if unsub is not None:
            cardiovascular_business["field_255"] = unsub

        return json.dumps(cardiovascular_business)

    def Health_Exec(self, Status, Update, cleaned=None, unsub=None):
        """
        HE_Status = 'field_248'
        HE_Update = 'field_297'
        HE_cleaned = 'field_258'
        HE_unsub = 'field_254
        """

        health_exec = {
            "field_248": Status,
            "field_297": Update,
        }

        if cleaned is not None:
            health_exec["field_258"] = cleaned

        if unsub is not None:
            health_exec["field_254"] = unsub

        return json.dumps(health_exec)

    def AI_Healthcare(self, Status, Update, cleaned=None, unsub=None):
        """
        AI_Status = 'field_242'
        AI_Update = 'field_296'
        AI_cleaned = 'field_245'
        AI_unsub = 'field_244'
        """

        ai_healthcare = {"field_242": Status, "field_296": Update}
        if cleaned is not None:
            ai_healthcare["field_245"] = cleaned

        if unsub is not None:
            ai_healthcare["field_244"] = unsub

        return json.dumps(ai_healthcare)

    def update_list_member(self, member_info):
        try:
            response = self.client.lists.set_list_member(
                member_info.get("list_id"),
                member_info.get("email_address"),
                {
                    "merge_fields": {
                        "KNACKDATE": str(datetime.date.today()),
                        "KNACKCHANG": member_info.get("last_changed"),
                    }
                },
            )
            print("mailchimp also updated")
        except ApiClientError as error:
            print("Error: {}".format(error.text))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("list_id", help="list_id", type=str)
    args = parser.parse_args()

    mailchimp_obj = MailchimpScripts(args.list_id)
    mailchimp_obj.get_list_member_info()
