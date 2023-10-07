<template>
  <span class="d-flex align-self-top justify-content-center align-items-center">
    <div class="input-group input-group-xs">
      <!-- day -->
      <button class="btn dropdown-toggle" type="button" data-bs-toggle="dropdown">{{ dayDisplay }}</button>
      <div class="dropdown-menu">
        <table class="table optiontable">
          <tr v-for="line in days" class="">
            <td v-for="day in line" >
              <span type="button" class="btn optionbutton" v-if="day != 0" @click="dayClicked(day)">{{ day }}</span> </td>
          </tr>
        </table>
      </div>
      <!-- month -->
      <button class="btn dropdown-toggle" type="button" data-bs-toggle="dropdown">{{ month+1 }}</button>
      <div class="dropdown-menu">
        <table class="table optiontable">
          <tr v-for="line in months" class="">
            <td v-for="month in line" class="p-0 m-0"> 
              <span type="button" class="btn btn-sm optionbutton">{{ month+1 }}</span> </td>
          </tr>
        </table>
      </div>
      <!-- year -->
      <button class="btn dropdown-toggle" type="button" data-bs-toggle="dropdown">{{ year }}</button>
      <div class="dropdown-menu">
        <table class="table optiontable">
          <tr v-for="myyear in years" class="">
            <td >
              <span type="button" class="btn optionbutton">{{ myyear }}</span> </td>
          </tr>
        </table>
      </div>
      <button class="button-outline-secondary" type="button" @click="updateDate"><span
          class="fa-solid fa-circle-check"></span></button>
    </div>
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatDate } from '@/assets/js/helpers'
import { graphData } from '../powerGraph/model';
const props = defineProps({
  modelValue: {
    type: Date,
    required: true
  },
  mode: {
    type: String,
    default:  'day'
  }
})
const thisYear = new Date().getFullYear()
  let years =  Array.from({length: 10}, (_,i) => thisYear-i)
const editMode = ref(true)
const  targetDate = ref(props.modelValue) 
const emit = defineEmits(['update:modelValue'])

// const days = Array.from({ length: 31 }, (_, i) => i + 1)
const months = [[0,1,2,3],[4,5,6,7],[8,9,10,11]]

let _day = props.modelValue.getDate()
let _month = props.modelValue.getMonth() + 1
let _year = props.modelValue.getFullYear()

const days = computed(() => {
  const newDate = new Date(year.value,month.value, 1)
  const firstWeekdayInMonth = newDate.getDay()
  let maxDaysPerMonth = 0;
  switch (month.value) {
    case 1:
    case 3:
    case 5:
    case 7:
    case 8:
    case 10:
    case 12:
      maxDaysPerMonth = 31
      break
    case 4:
    case 6:
    case 9:
    case 11:
      maxDaysPerMonth = 30
      break
    case 2: if ((Math.trunc(year.value / 4) * 4) == year.value) {
      maxDaysPerMonth = 29
    } else {
      maxDaysPerMonth == 28
    }
  }

  let result: number[][] = []
  let week = [0, 0, 0, 0, 0, 0, 0]
  let weekday = firstWeekdayInMonth
  for (let i = 0; i < maxDaysPerMonth; i++) {
    week[weekday] = i+1
    if (weekday == 6) {
      result.push(week)
      week = [0, 0, 0, 0, 0, 0, 0]
      weekday = 0
    } else {
    weekday++
    }
  }
  if (weekday < 8)
    result.push(week)

  return result
})

  
const day = computed({
  get() {
    return targetDate.value.getDate()
  },
  set(value: number) {
    targetDate.value.setDate (value)
  },
})
const month = computed({
  get() {
    return targetDate.value.getMonth()
  },
  set(value: number) {
    _month = value
  },
})
const year = computed({
  get() {
    return targetDate.value.getFullYear()
  },
  set(value: number) {
    _year = value
  },
})
function updateDate() {
  // let d = new Date(_year, _month - 1, _day)
  emit('update:modelValue', targetDate)
  editMode.value = false
}
function dayClicked (d: number) {
  targetDate.value.setDate(d)
}
function monthClicked (m: number) {
  targetDate.value.setMonth(m)
}
function yearClicked (y: number) {
  targetDate.value.setFullYear(y)
}
const dayDisplay = computed ( () => {
  return targetDate.value.getDate()
})
</script>

<style scoped>
.form-select {
  background-color: var(--color-input);
  border: 1;
  border-color: var(--color-bg);
  color: var(--color-bg);
  text-align: start;
  font-size: var(--font-small);
}

.commitbutton {
  background-color: var(--color-bg);
  color: var(--color-input);
}


option {
  color: green;
}

.form-select {
  font-size: var(--font-verysmall);

  background-color: var(--color-menu);
  color: var(--color-fg);
}
.optiontable {
  background-color: var(--color-menu);
}
.optionbutton {
  font-size: var(--font-small);
  color: var(--color-fg);
  background-color: var(--color-menu);
  font-size: var(--font-verysmall);
  text-align: center;
}
.dropdown-menu {
  background-color: var(--color-menu);
}
.dropdown-toggle {
  background-color: var(--color-menu);
  color: var(--color-fg);
  border: 1px solid var(--color-bg);
  font-size: var(--font-verysmall);
}
</style>
