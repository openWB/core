import{C as p}from"./HardwareInstallation-b6711c62.js";import{_ as l,u as n,k as d,l as c,G as t,E as i,y as r}from"./vendor-f90150d8.js";import"./vendor-fortawesome-8488187c.js";import"./index-84ae27ac.js";import"./vendor-bootstrap-99f0c261.js";import"./vendor-jquery-99ccf6d7.js";import"./vendor-axios-871a0510.js";import"./vendor-sortablejs-cfc19546.js";import"./dynamic-import-helper-be004503.js";const u={name:"DeviceSolarViewInverter",mixins:[p]},_={class:"device-solar-view-inverter"};function f(o,e,v,g,w,b){const s=n("openwb-base-heading"),a=n("openwb-base-text-input");return d(),c("div",_,[t(s,null,{default:i(()=>e[1]||(e[1]=[r(" Einstellungen für SolarView Wechselrichter ")])),_:1}),t(a,{title:"Kommando für die Abfrage",required:"","model-value":o.component.configuration.command,"onUpdate:modelValue":e[0]||(e[0]=m=>o.updateConfiguration(m,"configuration.command"))},{help:i(()=>e[2]||(e[2]=[r(" Kommandos gemäß SolarView-Dokumentation, z.B.: 00* (gesamte Anlage), 01* (Wechselrichter 1), 02* (Wechselrichter 2) ")])),_:1},8,["model-value"])])}const S=l(u,[["render",f],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/solar_view/solar_view/inverter.vue"]]);export{S as default};