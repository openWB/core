""" Modul, um die Daten vom Broker zu erhalten.
"""


class mqtt():
    """ Prozess, der die benötigten Topics abonniert, die Instanzen ertstellt, wenn z.b. ein Modul neu konfiguriert wird, 
    Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    #Instanzen
    cp_data=[]
    cp_template_data=[]
    pv_data=[]
    pv_module_data=[]
    ev_data=[]
    ev_template_data=[]
    ev_charge_template_data=[]
    meter_data=[]
    meter_module_data=[]
    bat_data=[]
    bat_module_data=[]
    evu_data=[]
    evu_module_data=[]
    sub_topics()

    def __init__(self):
        pass


    def handle_topics(self):
        """ wartet in einer Endlosschleife auf eingehende Topics und ruft Funktionen zur weiteren Verarbeitung auf.
        """

        ##Funktioniert das von der zeitlichen Reihenfolge? Man klickt ja eigentlich erst auf LP aktivieren, dann auf Vorlage verwenden.
        #keine Reihenfolge imner gucken, ob es Instanz schon gibt

        # if topic==/chargepoint/1:
        # 	if payload==1:
        #         cp1=chargepoint()
        # 		data.cp_data.append(cp1)
        # 	else
        # 		data.cp_data[0].remove(cp1)
        # elif topic == /chargepoint/1/config/template/autolock:
        #     if cp1 in data.cp_data:
        #         cp1=chargepoint()
        # 		data.cp_data.append(cp1)
        # 	if payload == active:
        # 		data.cp_data[0].autolock=true
        # 	else
        # 		data.cp_data[0].autolock=false
        # elif topic==/chargepoint/1/config/template:
        # 	if payload!="none":
        # 		data.cp_data[0].template=payload
        pass

    def sub_topics(self):
        """ abonniert alle Topics.
        """
        pass