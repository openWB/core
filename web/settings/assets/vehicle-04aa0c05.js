import{V as u}from"./VehicleConfig-f58abd3f.js";import{_ as a,u as s,k as d,l as p,G as i,E as r,y as l}from"./vendor-06e11d0e.js";import"./vendor-fortawesome-05d7e447.js";import"./index-28dff6dc.js";import"./vendor-bootstrap-4263d7eb.js";import"./vendor-jquery-9fc083b4.js";import"./vendor-axios-22b906fb.js";import"./vendor-sortablejs-0bb60e5b.js";import"./dynamic-import-helper-be004503.js";const m={name:"VehicleSocRenault",mixins:[u]},f={class:"vehicle-soc-renault"};function v(n,e,g,V,w,b){const t=s("openwb-base-text-input");return d(),p("div",f,[i(t,{title:"Benutzername",required:"",subtype:"user","model-value":n.vehicle.configuration.user_id,"onUpdate:modelValue":e[0]||(e[0]=o=>n.updateConfiguration(o,"configuration.user_id"))},{help:r(()=>e[4]||(e[4]=[l(" Der Benutzername für die Anmeldung an den Renault-Servern. ")])),_:1},8,["model-value"]),i(t,{title:"Kennwort",required:"",subtype:"password","model-value":n.vehicle.configuration.password,"onUpdate:modelValue":e[1]||(e[1]=o=>n.updateConfiguration(o,"configuration.password"))},{help:r(()=>e[5]||(e[5]=[l(" Das Passwort für die Anmeldung an den Renault-Servern. ")])),_:1},8,["model-value"]),i(t,{title:"Land",required:"","model-value":n.vehicle.configuration.country,"onUpdate:modelValue":e[2]||(e[2]=o=>n.updateConfiguration(o,"configuration.country"))},{help:r(()=>e[6]||(e[6]=[l(" Land des Fahrzeugs, z.b. DE für Deutschland. ")])),_:1},8,["model-value"]),i(t,{title:"VIN","model-value":n.vehicle.configuration.vin,"onUpdate:modelValue":e[3]||(e[3]=o=>n.updateConfiguration(o,"configuration.vin"))},{help:r(()=>e[7]||(e[7]=[l(" Die Fahrgestellnummer des Fahrzeugs falls mehrere Fahrzeuge im Account vorhanden sind. ")])),_:1},8,["model-value"])])}const $=a(m,[["render",v],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/vehicles/renault/vehicle.vue"]]);export{$ as default};