import { reactive } from "vue";
import { updateServer } from '@/assets/js/sendMessages'
class EtData {
    etPriceList = ''
    private _etMaxPrice = 20
    etCurrentPrice = 0
    isEtEnabled = false
    etProvider = ''
    get etMaxPrice () {
        return this._etMaxPrice
    }
    set etMaxPrice (max: number) {
        this._etMaxPrice = max
        updateServer ('etMaxPrice', max)
    }
    updateEtMaxPrice (max: number) {
        this._etMaxPrice = max
    }
}

export const etData = reactive(new EtData())