import{C as p}from"./HardwareInstallation-0477e3e2.js";import{_ as a,u as t,k as m,l,G as i,E as d,y as c}from"./vendor-809787c9.js";import"./vendor-fortawesome-e760f6db.js";import"./index-f9dddb60.js";import"./vendor-bootstrap-5ce91dd7.js";import"./vendor-jquery-49acc558.js";import"./vendor-axios-57a82265.js";import"./vendor-sortablejs-d99a4022.js";import"./dynamic-import-helper-be004503.js";const b={name:"DeviceVictronCounter",mixins:[p]},_={class:"device-victron-counter"};function f(o,e,g,v,C,V){const r=t("openwb-base-heading"),u=t("openwb-base-number-input"),s=t("openwb-base-button-group-input");return m(),l("div",_,[i(r,null,{default:d(()=>e[2]||(e[2]=[c(" Einstellungen für Victron Zähler ")])),_:1}),i(u,{title:"Modbus ID",required:"","model-value":o.component.configuration.modbus_id,min:"1",max:"255","onUpdate:modelValue":e[0]||(e[0]=n=>o.updateConfiguration(n,"configuration.modbus_id"))},null,8,["model-value"]),i(s,{title:"Messgerät",buttons:[{buttonValue:!1,text:"AC-In Victron GX"},{buttonValue:!0,text:"Energy Meter"}],"model-value":o.component.configuration.energy_meter,"onUpdate:modelValue":e[1]||(e[1]=n=>o.updateConfiguration(n,"configuration.energy_meter"))},null,8,["model-value"])])}const G=a(b,[["render",f],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/victron/victron/counter.vue"]]);export{G as default};