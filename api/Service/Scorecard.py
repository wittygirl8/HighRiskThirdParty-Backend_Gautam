import traceback

from utils.db import MSSQLConnection

db = MSSQLConnection()


class Scorecard:

    def test(self, data):  # tbd
        try:
            # YOUR CODE HERE
            return True, 'test', {}
        except Exception as e:
            print("Scorecard.test(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
