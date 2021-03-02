"""prüft, ob Zeitfenster aktuell sind
"""

import datetime


def set_date(now, begin, end):
    """ setzt das Datum auf das heutige Datum, bzw. falls der Endzeitpunkt am nächsten Tag ist, auf morgen

    Parameters
    ----------
    now : datetime
        aktuelles Datum und Uhrzeit
    begin : datetime
        Beginn des Zeitfensters
    end : datetime
        Ende des Zeitfensters

    Return
    ------
    begin, end: datetime
        Zeitfenster mit heutigen bzw. morgigen Datum
    """
    begin = begin.replace(now.year, now.month, now.day)
    end = end.replace(now.year, now.month, now.day)
    if begin > end:
        # Endzeit ist am nächsten Tag
        end = end + datetime.timedelta(days=1)
    return begin, end


def is_timeframe_valid(now, begin, end):
    """ überprüft, ob das Zeitfenster des Ladeplans aktuell ist.

    Parameters
    ----------
    now : datetime
        aktuelles Datum und Uhrzeit
    begin : datetime
        Beginn des Zeitfensters
    end : datetime
        Ende des Zeitfensters

    Returns
    -------
    True : aktuell
    False : nicht aktuell
    """
    if ((now < begin) == False) and ((now < end) == True):
        return True
    else:
        return False


def check_plans_timeframe(plans, hours=None):
    """ geht alle Pläne durch.

    Parameters
    ----------
    plans: dictionary
        Liste der Pläne, deren Zeitfenster geprüft werden sollen
    hours = None: int
        Stunden, die der Beginn vorher liegen soll; Werden keine Stunden angegeben, wird der Beginn dem Dictionary entnommen.

    Returns
    -------
    plan: erster aktiver Plan
    None: falls kein Plan aktiv ist
    """
    state = None
    try:
        for plan in plans:
            # Nur Keys mit dem Namen plan + Plannummer berücksichtigen
            if "plan" in plan:
                state = check_timeframe(plans[plan], hours)
                if state == True:
                    return plan

        if state == None:
            # log
            print("Keine aktiven Zeit-Pläne.")
        return None
    except KeyError as key:
        print("dictionary key", key, "doesn't exist in check_plans_timeframe")
        return None

def check_timeframe(plan, hours):
    """ schaut, ob Plne aktiv sind, prüft, ob das Zeitfenster aktuell ist.

    Parameters
    ----------
    plan: dictionary
        Plan dessen Zeitfenster geprüft werden soll
    hours = None: int
        Stunden, die der Beginn vorher liegen soll; Werden keine Stunden angegeben, wird der Beginn dem Dictionary entnommen.

    Returns
    -------
    True: Zeitfenster gültig
    False: Zeitfenster nicht gültig
    """
    state = None
    try:
        if plan["active"] == True:
            now = datetime.datetime.today()
            if hours == None:
                begin = datetime.datetime.strptime(plan["time"][0], '%H:%M')
                end = datetime.datetime.strptime(plan["time"][1], '%H:%M')
            else:
                end = datetime.datetime.strptime(plan["time"], '%H:%M')

            if plan["frequency"]["selected"] == "once":
                if hours == None:
                    beginDate = datetime.datetime.strptime(
                        plan["frequency"]["once"][0], "%y-%m-%d")
                    begin = begin.replace(
                        beginDate.year, beginDate.month, beginDate.day)
                    endDate = datetime.datetime.strptime(
                        plan["frequency"]["once"][1], "%y-%m-%d")
                else:
                    endDate = datetime.datetime.strptime(
                        plan["frequency"]["once"][0], "%y-%m-%d")
                    end = end.replace(
                        endDate.year, endDate.month, endDate.day)
                    begin = __calc_begin(end, hours)
                end = end.replace(
                    endDate.year, endDate.month, endDate.day)
                state = is_timeframe_valid(now, begin, end)

            elif plan["frequency"]["selected"] == "daily":
                if hours == None:
                    begin, end = set_date(now, begin, end)
                else:
                    end = end.replace(now.year, now.month, now.day)
                    begin = __calc_begin(end, hours)
                state = is_timeframe_valid(now, begin, end)

            elif plan["frequency"]["selected"] == "weekly":
                if hours == None:
                    if begin < end:
                        # Endzeit ist am gleichen Tag
                        if plan["frequency"]["weekly"][now.weekday()] == True:
                            begin, end = set_date(now, begin, end)
                            state = is_timeframe_valid(
                                now, begin, end)
                        else:
                            state = False
                    else:
                        if (plan["frequency"]["weekly"][now.weekday()] or plan["frequency"]["weekly"][now.weekday()+1]) == True:
                            begin, end = set_date(now, begin, end)
                            state = is_timeframe_valid(
                                now, begin, end)
                        else:
                            state = False
                else:
                    if plan["frequency"]["weekly"][now.weekday()] == True:
                        end = end.replace(endDate.year, endDate.month, endDate.day)
                        begin = __calc_begin(end, hours)
                        state = is_timeframe_valid(
                            now, begin, end)
                    else:
                        state = False
    except KeyError as key:
        print("dictionary key", key, "related to loop-object",
            plan, "doesn't exist in check_timeframe")
        return None
    return state

def __calc_begin(end, hours):
    """ berechnet den Zeitpunkt, der die angegebenen Stunden vor dem Endzeitpunkt liegt.
    
    Parameter
    ---------
    end: datetime
        Endzeitpunkt
    hours: int
        Stunden, die der Beginn vorher liegen soll

    Return
    ------
    datetime: berechneter Zeitpunkt
    """
    prev=datetime.timedelta(hours)
    return end - prev

def check_duration(plan, duration):
    """ prüft, ob der in angegebene Zeitpunkt abzüglich der Dauer jetzt ist.

    Paramter
    --------
    plan : dictionary
        Plan, für den geprüft werden soll, ob mit der Ladung begonnen werden soll

    duration: float
        vorraussichtliche Ladedauer

    Return
    ------
    True: Ladung sollte starten
    False: hat noch Zeit
    """
    try:
        now = datetime.datetime.today()
        end = datetime.datetime.strptime(plan["time"], '%H:%M')

        if plan["frequency"]["selected"] == "once":
            endDate = datetime.datetime.strptime(plan["frequency"]["once"][0], "%y-%m-%d")
            end = end.replace(endDate.year, endDate.month, endDate.day)
            return is_duration_valid(now, duration, end)

        elif plan["frequency"]["selected"] == "daily":
            end = end.replace(now.year, now.month, now.day)
            return is_duration_valid(now, duration, end)

        elif plan["frequency"]["selected"] == "weekly":
            if plan["frequency"]["weekly"][now.weekday()] == True:
                end = end.replace(now.year, now.month, now.day)
                return is_duration_valid(now, duration, end)
            else:
                return False
    except KeyError as key:
        print("dictionary key", key, "doesn't exist in check_duration")
        return False


def is_duration_valid(now, duration, end):
    """ prüft, ob der Endzeitpunkt der Ladung abzüglich der Ladedauer in den nächsten 5 Min liegt oder schon vorüber ist.

    Parameter
    ---------
    now: datetime
        aktuelles Datum und Uhrzeit

    duration: float 
        vorraussichtliche Ladedauer
    
    end: datetime
        Zeitpunkt, an dem die Ladung beendet sein soll

    Return
    ------
    2, int: Zeitpunkt ist um mehr als 5 Min überschritten worden, verbleibende Zeit in h
    1, 0: Ladung sollte starten
    0, 0: hat noch Zeit
    """
    delta = datetime.timedelta(hours=int(duration), minutes=((duration%1)*60))
    begin = end - delta
    difference = (now - begin).total_seconds()
    if difference > 0:
        remaining_time = duration-(difference/3600)
        return 2, remaining_time
    elif difference > (-300):
        return 1, 0
    else:
        return 0, 0

def is_list_valid(hourlist):
    """ prüft, ob eine der angegebenen Unix-Zeiten aktuell ist.

    Parameter
    ---------
    hourlist: list
        Liste mit Unix-Zeiten

    Return
    ------
    True: aktuelle Stunde ist in der Liste enthalten
    False: aktuelle Stunde ist nicht in der Liste enthalten
    """
    now = datetime.datetime.today()
    for hour in hourlist:
        timestamp = datetime.datetime.fromtimestamp(float(hour))
        if timestamp.hour == now.hour:
            return True
        else:
            return False