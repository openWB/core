import{_ as c,u as t,k as d,l as u,D as o,N as s,y as a,x as p,z as l}from"./vendor-f2b8aa6f.js";import"./vendor-sortablejs-2f1828d0.js";const _={name:"DeviceSunwaysInverter",emits:["update:configuration"],props:{configuration:{type:Object,required:!0},deviceId:{default:void 0},componentId:{required:!0}},methods:{updateConfiguration(e,n=void 0){this.$emit("update:configuration",{value:e,object:n})}}},f={class:"device-sunways-inverter"},m={class:"small"};function v(e,n,b,g,h,w){const r=t("openwb-base-heading"),i=t("openwb-base-alert");return d(),u("div",f,[o(r,null,{default:s(()=>[a(" Einstellungen für Sunways Wechselrichter "),p("span",m,"(Modul: "+l(e.$options.name)+")",1)]),_:1}),o(i,{subtype:"info"},{default:s(()=>[a(" Diese Komponente erfordert keine Einstellungen. ")]),_:1})])}const x=c(_,[["render",v],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/sunways/inverter.vue"]]);export{x as default};