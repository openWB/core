import{C as a}from"./HardwareInstallation-a0083e3a.js";import{_ as p,u as t,k as m,l,D as i,N as c,y as d}from"./vendor-f2b8aa6f.js";import"./vendor-fortawesome-71546160.js";import"./index-b0e5e618.js";import"./vendor-bootstrap-4ad604fa.js";import"./vendor-jquery-d3cb8fad.js";import"./vendor-axios-65ecee4b.js";import"./vendor-sortablejs-2f1828d0.js";import"./dynamic-import-helper-be004503.js";const _={name:"DeviceVictronCounter",mixins:[a]},b={class:"device-victron-counter"};function f(e,o,g,v,C,V){const r=t("openwb-base-heading"),u=t("openwb-base-number-input"),s=t("openwb-base-button-group-input");return m(),l("div",b,[i(r,null,{default:c(()=>[d(" Einstellungen für Victron Zähler ")]),_:1}),i(u,{title:"Modbus ID",required:"","model-value":e.component.configuration.modbus_id,min:"1",max:"255","onUpdate:modelValue":o[0]||(o[0]=n=>e.updateConfiguration(n,"configuration.modbus_id"))},null,8,["model-value"]),i(s,{title:"Messgerät",buttons:[{buttonValue:!1,text:"AC-In Victron GX"},{buttonValue:!0,text:"Energy Meter"}],"model-value":e.component.configuration.energy_meter,"onUpdate:modelValue":o[1]||(o[1]=n=>e.updateConfiguration(n,"configuration.energy_meter"))},null,8,["model-value"])])}const N=p(_,[["render",f],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/victron/victron/counter.vue"]]);export{N as default};