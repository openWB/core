# counter0
#        |
#        - cp3
#        - counter6
#                  |
#                   - cp4
#                   - cp5
#        - inverter1
#        - bat2
NESTED_HIERARCHY = [{"id": 0, "type": "counter",
                     "children": [
                         {"id": 3, "type": "cp", "children": []},
                         {"id": 6, "type": "counter",
                          "children": [
                              {"id": 4, "type": "cp", "children": []},
                              {"id": 5, "type": "cp", "children": []}]},
                         {"id": 1, "type": "inverter", "children": []},
                         {"id": 2, "type": "bat", "children": []}]}]
