#!/usr/bin/python3
# coding: utf8

#########################################################
#
# liest von aWATTar die stündlichen Preise für heute und morgen,
# erstellt daraus die Preislisten-Datei für den Graphen und
# Datei mit aktuell gültigem Strompreis
#
# erwartet von API Stundenpreise, d.h. für jede Stunde eine Preisauskunft
# setzt aktuellen Strompreis (und für kommende 9 Std) im Fehlerfall auf 99.99ct/kWh
#
# Aufruf als Main
# oder nach Import: update_pricedata(landeskennung, basispreis)
#
# param: Landeskennung (at/de)
# param: individueller Basispreis des Anschlusses (kann auch 0 sein)
# param: Debug-Level
#
# Preisliste in UTC und ct/kWh, Aufbau Datei:
# Zeile 1: Name des Moduls + Landeskennung z. B. aWATTar_de
# Zeile 2 ff: timestamp,price
#
# 2021 Michael Ortenstein
# This file is part of openWB
#
#########################################################

import os
import sys
import re
import json
from time import sleep
from datetime import datetime, date, timezone, timedelta
import requests
import atexit

from ...algorithm import data
from ...helpermodules import log
from ...helpermodules import pub

#########################################################
#
# Setup
#
#########################################################

MODULE_NAME = 'aWATTar'
LAENDERDATEN = {
    'at': {
        'url': 'https://api.awattar.at/v1/marketdata',
        # Berechnung Brutto-Arbeitspreis für Österreich nicht möglich, da wesentlich komplexer.
        # Antwort aWATTar:
        # In Österreich werden Netzentgelte/Abgaben ganz anderes behandelt und sind im Unterschied zu Deutschland
        # auch nicht Teil des Vertrages mit aWATTar. In Österreich haben wir keine Möglichkeit, die Netzentgelte
        # vorab eindeutig zu bestimmen und führen dies normalerweise auch nicht auf. Es ist in Österreich auch möglich,
        # dass die Netzentgelte nicht an uns, sondern direkt an den Netzbetreiber entrichtet werden.
        # In anderen Worten, leider kann man das Verfahren aus Deutschland in Österreich nicht anwenden.
        'umsatzsteuer': 1,
        'awattargebuehr': 0
    },
    'de': {
        'url': 'https://api.awattar.de/v1/marketdata',
        'umsatzsteuer': 1.19,
        'awattargebuehr': 0.25
    }
}

_module_starttime = 0

#########################################################
#
# private Hilfsfunktionen
#
#########################################################

def _check_args(arg1, arg2):
    # arg1_str = re.sub('[^A-Za-z]+', '', arg1)  # Landeskennung
    # if not arg1_str in LAENDERDATEN:
    #     raise ValueError('1. Parameter (Landeskennung = "' + arg1_str + '") unbekannt')
    # arg2_str = re.sub('[^0-9.,]', '', arg2)  # Basispreis
    # try:
    #     arg2_float = float(arg2_str)
    # except:
    #     raise ValueError('2. Parameter (Basispreis = "' + arg2_str + '") ist keine Zahl') from None
    # return arg1, arg2_float
    pass

def _read_args():
    # gibt Kommandozeilenparameter zurück
    if len(sys.argv) == 4:
        # sys.argv[0] : erstes Argument ist immer Dateiname
        try:
            landeskennung, basispreis = _check_args(sys.argv[1], sys.argv[2], sys.argv[3])
        except:
            raise
    else:
        raise ValueError('Parameteranzahl falsch (' + str(len(sys.argv) - 1) + ' uebergeben aber 3 gefordert)')
    return landeskennung, basispreis

def _publish_price_data(pricelist_to_publish, current_module_name):
    # schreibt Preisliste und aktuellen Preis in Dateien und veröffentlicht die MQTT-Topics
    data.data.optional_data["optional"].data["et"]["get"]["source"] = current_module_name
    data.data.optional_data["optional"].data["et"]["get"]["price_list"] = pricelist_to_publish
    data.data.optional_data["optional"].data["et"]["get"]["price"] = pricelist_to_publish[0][1]
    pub.pub("openWB/set/optional/et/get/source", data.data.optional_data["optional"].data["et"]["get"]["source"])
    pub.pub("openWB/set/optional/et/get/price_list", data.data.optional_data["optional"].data["et"]["get"]["price_list"])
    pub.pub("openWB/set/optional/et/get/price", data.data.optional_data["optional"].data["et"]["get"]["price"])

def _exit_on_invalid_price_data(error, current_module_name):
    # schreibt 99.99ct/kWh in Preis-Datei und füllt Chart-Array für die nächsten 9 Stunden damit,
    # schreibt Fehler ins Log
    pricelist_to_publish = []
    now = datetime.now(timezone.utc)  # timezone-aware datetime-object in UTC
    timestamp = now.replace(minute=0, second=0, microsecond=0)  # volle Stunde
    for i in range(9):
        pricelist_to_publish.append([99.99, timestamp.timestamp()])
        timestamp = timestamp + timedelta(hours=1)
    log.message_debug_log("error", 'Fehler bei aWATTar-Preisbfrage: Setze Preis auf 99.99ct/kWh.')
    #publish MQTT-Daten für Preis und Graph
    data.data.optional_data["optional"].data["et"]["get"]["source"] = current_module_name
    data.data.optional_data["optional"].data["et"]["get"]["price_list"] = pricelist_to_publish
    data.data.optional_data["optional"].data["et"]["get"]["price"] = 99.99
    pub.pub("openWB/set/optional/et/get/source", data.data.optional_data["optional"].data["et"]["get"]["source"])
    pub.pub("openWB/set/optional/et/get/price_list", data.data.optional_data["optional"].data["et"]["get"]["price_list"])
    pub.pub("openWB/set/optional/et/get/price", data.data.optional_data["optional"].data["et"]["get"]["price"])
    exit()

def _try_api_call(max_tries=3, delay=5, backoff=2, exceptions=(Exception,), hook=None):
    #  copied from https://gist.github.com/n1ywb/2570004,
    #  adfjusted to be used with python3
    #
    #  Copyright 2012 by Jeff Laughlin Consulting LLC
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in
    # all copies or substantial portions of the Software.
    """Function decorator implementing retrying logic.
    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception, delay);
          default None
    The decorator will call the function up to max_tries times if it raises
    an exception.
    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.
    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = list(range(max_tries))
            tries.reverse()
            for tries_remaining in tries:
                log.message_debug_log("debug", 'Abfrage aWATTar-API')
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        log.message_debug_log("error", "Fehler bei der aWATTar-API-Abfrage, "+str(tries_remaining)+" Versuche übrig, versuche erneut in "+str(mydelay)+" Sekunden")
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec

@_try_api_call()
def _readAPI(url):
    # Timeout für Verbindung = 2 sek und Antwort = 6 sek
    response = requests.get(url, headers={'Content-Type': 'application/json'}, timeout=(2, 6))
    return response

def _get_utcfromtimestamp(timestamp):
    # erwartet timestamp Typ float
    # gibt timezone-aware Datetime-Objekt zurück in UTC
    datetime_obj = datetime.utcfromtimestamp(timestamp)  # Zeitstempel von String nach Datetime-Objekt
    datetime_obj = datetime_obj.replace(tzinfo=timezone.utc)  # Objekt von naive nach timezone-aware, hier UTC
    return datetime_obj

def _cleanup_pricelist(pricelist):
    # bereinigt Preisliste, löscht Einträge die älter als aktuelle Stunde sind
    # und über morgen hinausgehen
    # wenn der erste Preis nicht für die aktuelle Stunde ist, wird leere Liste zurückgegeben
    # prüft auf Abstand der Preise: ist dieser >1h, wird Liste ab diesem Punkt abgeschnitten
    if len(pricelist) > 0:
        now = datetime.now(timezone.utc)  # timezone-aware datetime-object in UTC
        now_full_hour = now.replace(minute=0, second=0, microsecond=0)  # volle Stunde
        now_full_hour_timestamp = datetime.timestamp(now_full_hour)
        # zuerst filtern auf "ab diese Stunde" bis "längstens morgen"
        for index, price in enumerate(pricelist[:]):  # über Kopie der Liste iterieren, um das Original zu manipulieren
            try:
                starttime_utc = _get_utcfromtimestamp(float(price[0]))  # Start-Zeitstempel aus Preisliste umwandeln
            except:
                raise TypeError('Zeitstempel-Umwandlung fehlgeschlagen') from None
            # ältere als aktuelle Stunde und weiter als morgen löschen
            if (float(price[0]) < now_full_hour_timestamp) or (starttime_utc.date() > now.date() + timedelta(days=1)):
                pricelist.remove(price)
        # jetzt prüfen auf Start mit aktueller Stunde und Stundenabstände
        if len(pricelist) > 0:
            timestamp_prev = float(pricelist[0][0])  # erster Listeneintrag
            starttime_utc = _get_utcfromtimestamp(float(pricelist[0][0]))
            if _get_utcfromtimestamp(timestamp_prev) == now_full_hour:  # erster Preis ist der von aktueller Stunde
                for index, price in enumerate(pricelist[:]):  # über Kopie der Liste iterieren, um das Original zu manipulieren
                    if index > 0:
                        timestamp = float(price[0])
                        secondsdiff = timestamp - timestamp_prev
                        timestamp_prev = float(price[0])
                        if secondsdiff != 3600.0:  # ist Abstand <> 1h dann ab hier Liste löschen
                            del pricelist[index:]
                            break
            else:
                return []
            return pricelist
    return []

def _get_updated_pricelist(landeskennung, basispreis):
    # API abfragen, retry bei Timeout
    # Rückgabe ist empfangene bereinigte Preisliste mit aktuellem Preis als ersten Eintrag
    # Bei Fehler oder leerer Liste wird Exception geworfen
    # Da aWATTar pro Abruf nur max. 24h Preise liefert, benötigt man für eine komplette Liste
    # einschl. aller morgiger Preise 2 Abfragen
    #
    # zunächst Abfragen der heutigen Preise in local-time
    date_obj = datetime.now()
    start_obj = date_obj.replace(minute=0, second=0, microsecond=0)  # aktuelle volle Stunde
    start_timestamp = start_obj.timestamp() * 1000
    date_obj = date_obj + timedelta(days=1)
    end_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)  # Mitternacht
    end_timestamp = end_obj.timestamp() * 1000
    api_url = LAENDERDATEN[landeskennung]['url'] + '?start=' + str('%d' % start_timestamp) + '&end=' + str('%d' % end_timestamp)
    # Abfrage der Preise bis Mitternacht
    try:
        response = _readAPI(api_url)
    except:
        raise RuntimeError('Fataler Fehler bei API-Abfrage') from None
    log.message_debug_log("debug", 'Antwort auf Abfrage erhalten')
    # sind sonstige-Fehler aufgetreten?
    try:
        response.raise_for_status()
    except:
        raise
    # Bei Erfolg JSON auswerten
    log.message_debug_log("debug", 'Ermittle JSON fuer heutige Preise aus aWATTar-Antwort')
    try:
        marketprices = json.loads(response.text)['data']
    except:
        raise RuntimeError('Korruptes JSON') from None
    log.message_debug_log("debug", "aWATTar-Preisliste fuer heute extrahiert")
    # dann Abfragen der morgigen Preise in local-time
    start_timestamp = end_timestamp  # Mitternacht
    end_obj = end_obj + timedelta(days=1) # Mitternacht Übermorgen
    end_timestamp = end_obj.timestamp() * 1000
    api_url = LAENDERDATEN[landeskennung]['url'] + '?start=' + str('%d' % start_timestamp) + '&end=' + str('%d' % end_timestamp)
    # Abfrage der Preise morgen bis Mitternacht
    try:
        response = _readAPI(api_url)
    except:
        raise RuntimeError('Fataler Fehler bei API-Abfrage') from None
    log.message_debug_log("debug", 'Antwort auf Abfrage erhalten')
    # sind sonstige-Fehler aufgetreten?
    try:
        response.raise_for_status()
    except:
        raise
    # Bei Erfolg JSON auswerten
    log.message_debug_log("debug", 'Ermittle JSON fuer morgige Preise aus aWATTar-Antwort')
    try:
        marketprices = marketprices + json.loads(response.text)['data']
    except:
        raise RuntimeError('Korruptes JSON') from None
    log.message_debug_log("debug", "aWATTar-Preisliste für morgen extrahiert")

    # alle Zeiten in UTC verarbeiten
    now = datetime.now(timezone.utc)  # timezone-aware datetime-object in UTC
    now_full_hour = now.replace(minute=0, second=0, microsecond=0)  # volle Stunde
    log.message_debug_log("debug", 'Formatiere und analysiere Preisliste')
    pricelist = []
    for price_data in marketprices:
        startzeit_utc = _get_utcfromtimestamp(price_data['start_timestamp']/1000)  # Zeitstempel kommt von API in UTC mit Millisekunden, UNIX ist ohne
        if landeskennung == 'de':
            if basispreis == 0:
                # Kein Basispreis, dann nur Anzeige des Börsenpreises [ct/kWh] ohne weitere Bestandteile
                bruttopreis = price_data['marketprice']/10
            else:
                # Bruttopreis Deutschland [ct/kWh] = ((marketpriceAusAPI/10) * 1.19) + Awattargebühr + Basispreis
                bruttopreis = (price_data['marketprice']/10 * LAENDERDATEN[landeskennung]['umsatzsteuer']) + LAENDERDATEN[landeskennung]['awattargebuehr'] + basispreis
            bruttopreis_str = round(bruttopreis, 2)
        else:
            # für Österreich keine Berechnung möglich, daher nur marketpriceAusAPI benutzen
            bruttopreis_str = round(price_data['marketprice']/10, 2)
        pricelist.append([startzeit_utc.timestamp(), bruttopreis_str])
    try:
        pricelist = _cleanup_pricelist(pricelist)
    except:
        raise
    if len(pricelist) == 0:
        raise RuntimeError('Aktueller Preis konnte nicht ermittelt werden')
    else:
        log.message_debug_log("info", "AaWATTar: aktueller Preis ist "+str(pricelist[0][1])+" ct/kWh")
    return pricelist

def _get_existing_pricelist():
    # liest vorhanden Preisliste aus Datei
    # return: Preisliste, Name des Moduls verantwortlich für Preisliste
    existing_pricelist = []  # vorhandene Liste
    try:
        module_name_in_file = data.data.optional_data["optional"].data["et"]["get"]["source"]
        module_name_in_file = re.sub('[^A-Za-z0-9_-]', '', module_name_in_file)  # ggf. unerwünschte Zeichen entfernen
        existing_pricelist = data.data.optional_data["optional"].data["et"]["get"]["price_list"]
    except:
        raise
    return existing_pricelist, module_name_in_file

def _convert_timestamp_to_str(timestamp):
    # konvertiert timestamp in UTC zu String (in Lokalzeit) Format: 11.01., 23:00 Uhr
    # ist das Datum heute, dann Format heute, 23:00 Uhr
    # ist das Datum morgen, dann Format morgen, 23:00 Uhr
    today = date.today()
    tomorrow = today + timedelta(days=1)
    datetime_obj = _get_utcfromtimestamp(timestamp)
    datetime_obj = datetime_obj.astimezone(tz=None)  # und nach lokal
    if today == datetime_obj.date():
        the_date = 'heute, '
    elif tomorrow == datetime_obj.date():
        the_date = 'morgen, '
    else:
        the_date = datetime_obj.strftime('%d.%m., ')
    the_time = datetime_obj.strftime('%H:%M Uhr')
    return (the_date + the_time)

def _log_module_runtime():
    # schreibt Modullaufzeit ins Logfile
    runtime = datetime.now() - _module_starttime
    runtime = runtime.total_seconds()
    log.message_debug_log("debug", 'Modullaufzeit ' + str(runtime) + ' s')

#########################################################
#
# öffentliche Funktion
#
#########################################################

def update_pricedata(landeskennung, basispreis):
    global _module_starttime

    _module_starttime = datetime.now()
    # bei exit immer Laufzeit des Moduls bestimmen, Funktion aber nicht doppelt registrieren
    atexit.register(_log_module_runtime)
    if __name__ != '__main__':
        try:
            _check_args(landeskennung, basispreis)
        except Exception as e:
            _exit_on_invalid_price_data('Modul-Abbruch: ' + str(e), MODULE_NAME)

    log.message_debug_log("debug", 'Lese bisherige Preisliste')
    pricelist_in_file = []
    module_name_in_file = None
    try:
        pricelist_in_file, module_name_in_file = _get_existing_pricelist()
    except Exception as e:
        log.exception_logging(e)
        log.message_debug_log("error", "aWATTar: Vorhandene Preisliste konnte nicht gelesen werden, versuche Neuerstellung")

    current_module_name = MODULE_NAME + '_' + landeskennung
    if len(pricelist_in_file) > 0 and pricelist_in_file[0][1] == '99.99':
        log.message_debug_log("debug", "Bisherige Preisliste enthaelt nur Fehlerpreise 99.99ct/kWh. Versuche, neue Preise von aWATTar zu empfangen.")
    elif module_name_in_file != None and current_module_name != module_name_in_file:
        if module_name_in_file == '':
            log_text = 'Kein Modul für bisherige Preisliste identifizierbar'
        else:
            log_text = 'Bisherige Preiliste wurde von Modul ' + module_name_in_file + ' erstellt'
        log.message_debug_log("debug", log_text)
        log.message_debug_log("debug", 'Wechsel auf Modul '+current_module_name)
    elif len(pricelist_in_file) > 0:
        log.message_debug_log("debug", 'Bisherige Preisliste gelesen')
        # Modul der bisherigen Liste ist mit diesem identisch, also Einträge in alter Preisliste benutzen und aufräumen
        prices_count_before_cleanup = len(pricelist_in_file)
        log.message_debug_log("debug", 'Bereinige bisherige Preisliste')
        try:
            pricelist_in_file = _cleanup_pricelist(pricelist_in_file)
        except Exception as e:
            log.exception_logging(e)
            log.message_debug_log("debug", "Vorhandene Preisliste nicht nutzbar")
            pricelist_in_file = []

        if len(pricelist_in_file) > 0:
            prices_count_after_cleanup = len(pricelist_in_file)
            log.message_debug_log("debug", 'Bisherige Preisliste bereinigt')
            prices_count_diff = prices_count_before_cleanup - prices_count_after_cleanup
            if prices_count_diff == 0:
                log.message_debug_log("debug", 'Es wurde kein Preis geloescht')
            elif prices_count_diff == 1:
                log.message_debug_log("debug", 'Es wurde 1 Preis geloescht')
            elif prices_count_diff > 1:
                log.message_debug_log("debug", 'Es wurden '+str(prices_count_diff)+' Preise geloescht')
            if prices_count_after_cleanup > 0:
                # mindestens der aktuelle Preis ist in der Liste
                log.message_debug_log("debug", "Bisherige Preisliste hat noch "+str(prices_count_after_cleanup)+" Eintraege")
                pricelist_valid_until_str = _convert_timestamp_to_str(float(pricelist_in_file[-1][0]))  # timestamp von letztem Element in Liste
                log.message_debug_log("debug", 'Letzter Preis in bisherige Preisliste gueltig ab ' + pricelist_valid_until_str)
                if prices_count_after_cleanup < 11:
                    # mit 10 Preisen des Tages übrig: gegen 14 Uhr gibt es neue Preise
                    log.message_debug_log("debug", 'Versuche, weitere Preise von aWATTar zu empfangen')
                    pricelist_received = []
                    try:
                        pricelist_received = _get_updated_pricelist(landeskennung, basispreis)
                    except Exception as e:
                        log.exception_logging(e)
                    if len(pricelist_received) > 0:
                        log.message_debug_log("debug", 'Abfrage der Preise erfolgreich')
                        log.message_debug_log("debug", 'Abgefragte Preisliste hat '+str(len(pricelist_received))+' Eintraege')
                        pricelist_valid_until_str = _convert_timestamp_to_str(float(pricelist_received[-1][0]))  # timestamp von letztem Element in Liste
                        log.message_debug_log("debug", 'Letzter Preis in abgefragter Preisliste gueltig ab ' + pricelist_valid_until_str)
                        prices_count_diff = len(pricelist_received) - prices_count_after_cleanup
                        if prices_count_diff == 0:
                            log.message_debug_log("debug", 'Keine neuen Preise empfangen')
                            log.message_debug_log("debug", 'Bereinigte bisherige Preisliste wird weiter verwendet')
                        elif prices_count_diff < 0:
                            log.message_debug_log("debug", 'Empfangene Preisliste kuerzer als bereits vorhandene')
                            log.message_debug_log("debug", 'Bereinigte bisherige Preisliste wird weiter verwendet')
                        else:
                            log.message_debug_log("debug", str(prices_count_diff)+' zusaetzliche Preise empfangen')
                            log.message_debug_log("debug", 'Publiziere Preisliste')
                            _publish_price_data(pricelist_received, current_module_name)
                            exit()
                    else:
                        log.message_debug_log("debug", 'Abfrage weiterer Preise nicht erfolgreich')
                else:
                    log.message_debug_log("debug", 'Ausreichend zukuenftige Preise in bisheriger Preisliste')
                # bisherige Liste hat ausreichend Preise für die Zukunft bzw.
                # mindestens den aktuellen Preis und Fehler bei der API-Abfrage
                if prices_count_before_cleanup - prices_count_after_cleanup > 0:
                    # es wurden Preise aus der bisherigen Liste bereinigt, also veröffentlichen
                    log.message_debug_log("debug", 'Verwende Preise aus bereinigter bisheriger Preisliste')
                    log.message_debug_log("debug", 'Publiziere Preisliste')
                    _publish_price_data(pricelist_in_file, current_module_name)
                exit()

    # bisherige Preisliste leer, fehlerhaft oder neuer Provider: in jedem Fall neue Abfrage und
    # bei andauerndem Fehler oder weiterhin leerer Liste Preis auf 99.99ct/kWh setzen
    try:
        pricelist_received = _get_updated_pricelist(landeskennung, basispreis)
    except Exception as e:
        _exit_on_invalid_price_data(str(e), current_module_name)
    # Preisliste enthält mindestens den aktuellen Preis
    pricelist_valid_until_str = _convert_timestamp_to_str(float(pricelist_received[-1][0]))  # timestamp von letztem Element in Liste
    log.message_debug_log("debug", 'Letzter Preis in abgefragter Preisliste gueltig ab ' + pricelist_valid_until_str)
    msg = 'Publiziere Preisliste mit ' + str(len(pricelist_received))
    if len(pricelist_received) == 1:
        msg += ' Preis'
    else:
        msg += ' Preisen'
    log.message_debug_log("debug", msg)
    _publish_price_data(pricelist_received, current_module_name)

#########################################################
#
# Main:
#
#########################################################

def awattar_get_prices():
    try:
        landeskennung, basispreis = _read_args()
    except Exception as e:
        _exit_on_invalid_price_data('Modul-Abbruch: ' + str(e), MODULE_NAME)

    update_pricedata(landeskennung, basispreis)
