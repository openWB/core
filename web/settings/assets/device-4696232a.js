import{D as a}from"./HardwareInstallation-70f156e6.js";import{_ as d,u as s,k as u,l as p,D as t,N as l,y as m}from"./vendor-a21b3a62.js";import"./vendor-fortawesome-41164876.js";import"./index-f9fda857.js";import"./vendor-bootstrap-d0c3645c.js";import"./vendor-jquery-a5dbbab1.js";import"./vendor-axios-0e6de98a.js";import"./vendor-sortablejs-3016fed8.js";import"./dynamic-import-helper-be004503.js";const f={name:"DeviceBYD",mixins:[a]},v={class:"device-byd"};function b(o,e,c,g,_,w){const r=s("openwb-base-heading"),i=s("openwb-base-text-input");return u(),p("div",v,[t(r,null,{default:l(()=>e[3]||(e[3]=[m(" Einstellungen für BYD ")])),_:1}),t(i,{title:"IP oder Hostname",subtype:"host",required:"","model-value":o.device.configuration.ip_address,"onUpdate:modelValue":e[0]||(e[0]=n=>o.updateConfiguration(n,"configuration.ip_address"))},null,8,["model-value"]),t(i,{title:"Benutzername",subtype:"user",required:"","model-value":o.device.configuration.user,"onUpdate:modelValue":e[1]||(e[1]=n=>o.updateConfiguration(n,"configuration.user"))},null,8,["model-value"]),t(i,{title:"Passwort",subtype:"password",required:"","model-value":o.device.configuration.password,"onUpdate:modelValue":e[2]||(e[2]=n=>o.updateConfiguration(n,"configuration.password"))},null,8,["model-value"])])}const N=d(f,[["render",b],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/byd/byd/device.vue"]]);export{N as default};