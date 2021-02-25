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


def check_timeframe(plans):
    """ geht alle Pläne durch, schaut, ob sie aktiv sind, prüft, ob das Zeitfenster aktuell ist und ob sich Pläne widersprechen.

    Parameters
    ----------
    plan : dictionary
        Plan, dessen Zeitfenster geprüft werden soll

    Returns
    -------
    plan: erster aktiver Plan
    None: falls kein Plan aktiv ist
    """
    state = None
    try:
        for plan in plans:
            # Nur Keys mit dem Namen plan + Plannummer berücksichtigen
            try:
                if "plan" in plan:
                    if plans[plan]["active"] == True:
                        now = datetime.datetime.today()
                        begin = datetime.datetime.strptime(
                            plans[plan]["time"][0], '%H:%M')
                        end = datetime.datetime.strptime(plans[plan]["time"][1], '%H:%M')

                        if plans[plan]["frequency"]["selected"] == "once":
                            beginDate = datetime.datetime.strptime(
                                plans[plan]["frequency"]["once"][0], "%y-%m-%d")
                            endDate = datetime.datetime.strptime(
                                plans[plan]["frequency"]["once"][1], "%y-%m-%d")
                            begin = begin.replace(
                                beginDate.year, beginDate.month, beginDate.day)
                            end = end.replace(
                                endDate.year, endDate.month, endDate.day)
                            state = is_timeframe_valid(now, begin, end)

                        elif plans[plan]["frequency"]["selected"] == "daily":
                            begin, end = set_date(now, begin, end)
                            state = is_timeframe_valid(now, begin, end)

                        elif plans[plan]["frequency"]["selected"] == "weekly":
                            if begin < end:
                                # Endzeit ist am gleichen Tag
                                if plans[plan]["frequency"]["weekly"][now.weekday()] == True:
                                    begin, end = set_date(now, begin, end)
                                    state = is_timeframe_valid(
                                        now, begin, end)
                                else:
                                    state = False
                            else:
                                if (plans[plan]["frequency"]["weekly"][now.weekday()] or plans[plan]["frequency"]["weekly"][now.weekday()+1]) == True:
                                    begin, end = set_date(now, begin, end)
                                    state = is_timeframe_valid(
                                        now, begin, end)
                                else:
                                    state = False

                        if state == True:
                            return plan
            except:
                print("dictionary key related to loop-object",
                    plan, "doesn't exist in check_timeframe")
                return None

        if state == None:
            # log
            print("Keine aktiven Zeit-Pläne.")
        return None
    except:
        print("dictionary key doesn't exist in check_timeframe")
        return None
