<!-- vue templates start here -->
<script type="text/x-template" id="text-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<div class="input-group">
					<div class="input-group-prepend">
						<div class="input-group-text">
							<i v-if="subtype == 'text'" class="fas fa-fw fa-keyboard"></i>
							<i v-if="subtype == 'email'" class="fa fa-fw fa-envelope"></i>
							<i v-if="subtype == 'host'" class="fas fa-fw fa-network-wired"></i>
							<i v-if="subtype == 'url'" class="fas fa-fw fa-globe"></i>
							<i v-if="subtype == 'user'" class="fa fa-fw fa-user"></i>
							<i v-if="subtype == 'json'" class="fas fa-fw fa-code"></i>
							<i v-if="subtype == 'password'" class="fa fa-fw" :class="showPassword ? 'fa-unlock' : 'fa-lock'"></i>
						</div>
					</div>
					<input v-if="['text', 'user', 'json'].includes(subtype)" type="text" class="form-control" v-model="value" v-bind="$attrs" :pattern="pattern">
					<input v-if="subtype == 'password'" :type="showPassword ? 'text' : 'password'" class="form-control" v-model="value" v-bind="$attrs" :pattern="pattern">
					<input v-if="subtype == 'host'" type="text" class="form-control" pattern="^(((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])|[A-Za-z0-9\._\-]*)$" v-model="value" v-bind="$attrs">
					<input v-if="['email', 'url'].includes(subtype)" :type="subtype" class="form-control" v-model="value" v-bind="$attrs">
					<div v-if="subtype == 'password'" class="input-group-append" v-on:click="togglePassword">
						<div class="input-group-text">
							<i class="far fa-fw" :class="showPassword ? 'fa-eye' : 'fa-eye-slash'"></i>
						</div>
					</div>
				</div>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="number-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<div class="input-group">
					<div class="input-group-prepend">
						<div class="input-group-text">
							<i class="fas fa-fw fa-calculator"></i>
						</div>
					</div>
					<input type="number" class="form-control" :min="min" :max="max" :step="step" v-model.number="value" v-bind="$attrs">
					<div v-if="unit" class="input-group-append">
						<div class="input-group-text">
							{{ unit }}
						</div>
					</div>
				</div>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="range-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row vaRow mb-1">
				<label v-if="label" for="XXX" class="col-2 col-form-label valueLabel">{{ label }}</label>
				<button class="col-1 btn btn-block btn-info" type="button" @click="decrement">
					<i class="fas fa-step-backward"></i>
				</button>
				<div class="col">
					<input type="range" class="form-control-range rangeInput" :min="min" :max="max" :step="step" v-model.number="sliderValue" v-bind="$attrs">
				</div>
				<button class="col-1 btn btn-block btn-info" type="button" @click="increment">
					<i class="fas fa-step-forward"></i>
				</button>
			</div>
			<div v-if="showHelp" class="form-row alert alert-info my-1 small">
				<div class="col">
					<slot name="help"></slot>
				</div>
			</div>
		</div>
	</div>
</script>

<script type="text/x-template" id="textarea-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<textarea class="form-control" v-model="value" v-bind="$attrs"></textarea>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="select-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<select class="form-control" v-model="value" v-bind="$attrs">
					<!-- select elements without option groups -->
					<option v-for="(option) in options" :value="option.value">{{ option.text }}</option>
					<!-- option groups with options -->
					<optgroup v-for="(group) in groups" :label="group.label">
						<option v-for="(option) in group.options" :value="option.value">{{ option.text }}</option>
					</optgroup>
				</select>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="buttongroup-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<div class="btn-group btn-block btn-group-toggle">
					<label v-for="button in buttons" class="btn" :class="[ value == button.buttonValue ? 'active' : '', button.class ? button.class : 'btn-outline-info' ]">
						<input type="radio" v-model="value" :value="button.buttonValue">{{ button.text }}
						<i :class="[ button.icon ? button.icon : 'fas fa-check' ]" :style="[ value == button.buttonValue ? 'visibility: visible' : 'visibility: hidden' ]"></i>
					</label>
				</div>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="checkbox-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<input class="form-control" type="checkbox" v-model="value" v-bind="$attrs">
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="alert-template">
	<div class="card-text alert" :class="'alert-'+subtype">
		<slot></slot>
	</div>
</script>

<script type="text/x-template" id="heading-template">
	<div class="card-text">
		<slot></slot>
	</div>
</script>

<script type="text/x-template" id="submit-buttons-template">
	<div class="row justify-content-center">
		<div class="col-md-4 d-flex py-1 justify-content-center">
			<button id="saveSettingsBtn" type="button" class="btn btn-block btn-success" @click="saveSettings()">Speichern</button>
		</div>
		<div class="col-md-4 d-flex py-1 justify-content-center">
			<button id="modalResetBtn" type="button" class="btn btn-block btn-warning" @click="showResetModal()">Änderungen verwerfen</button>
		</div>
		<div class="col-md-4 d-flex py-1 justify-content-center">
			<button id="modalDefaultsBtn" type="button" class="btn btn-block btn-danger" @click="showDefaultsModal()">Werkseinstellungen</button>
		</div>
	</div>
</script>

<script type="text/x-template" id="card-template">
	<div class="card" :class="'border-'+subtype">
		<div class="card-header" :class="'bg-'+subtype">
			<div class="form-group mb-0">
				<div class="form-row vaRow mb-1">
					<div class="col">
						{{ title }}
					</div>
				</div>
			</div>
		</div>
		<div class="card-body">
			<slot></slot>
		</div>
	</div>
</script>

<script type="text/x-template" id="page-footer-template">
	<footer id="footer" class="footer bg-dark text-light font-small">
		<div class="container text-center">
			<small>Sie befinden sich hier: Einstellungen / {{ location }}</small>
		</div>
	</footer>
</script>

<script type="text/x-template" id="donation-banner-template">
	<div class="mt-3 alert alert-dark text-center">
		Open Source made with love!<br>
		Jede Spende hilft die Weiterentwicklung von openWB voranzutreiben<br>
		<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
			<input type="hidden" name="cmd" value="_s-xclick">
			<input type="hidden" name="hosted_button_id" value="2K8C4Y2JTGH7U">
			<button type="submit" class="btn btn-warning">Spenden <i class="fab fa-paypal"></i></button>
		</form>
	</div>
</script>

<script type="text/x-template" id="content-template">
	<!-- common modal dialogues start here >>> -->
	<!-- save-in-progress overlay -->
	<div id="saveprogress" class="hide">
		<div id="saveprogress-inner">
			<div class="row">
				<div class="mx-auto d-block justify-content-center">
					<img id="saveprogress-image" src="img/favicons/preloader-image.png" alt="openWB">
				</div>
			</div>
			<div id="saveprogress-info" class="row justify-content-center mt-2">
				<div class="col-10 col-sm-6">
					Bitte warten, geänderte Einstellungen werden gespeichert.
				</div>
			</div>
		</div>
	</div>

	<!-- modal set-defaults-confirmation window -->
	<div class="modal fade" id="setDefaultsConfirmationModal" role="dialog">
		<div class="modal-dialog" role="document">
			<div class="modal-content">
				<!-- modal header -->
				<div class="modal-header bg-danger">
					<h4 class="modal-title text-light">Achtung</h4>
				</div>
				<!-- modal body -->
				<div class="modal-body text-center">
					<p>
						Alle Einstellungen auf dieser Seite werden auf die Werkseinstellungen zurückgesetzt.<br>
						Sie müssen anschließend auf "Speichern" klicken, um die Werte zu übernehmen.
					</p>
					<p>
						Sollen die übergreifenden Ladeeinstellungen wirklich auf Werkseinstellungen zurückgesetzt werden?
					</p>
				</div>
				<!-- modal footer -->
				<div class="modal-footer d-flex justify-content-center">
					<button type="button" class="btn btn-success" data-dismiss="modal" @click="setDefaultValues">Fortfahren</button>
					<button type="button" class="btn btn-danger" data-dismiss="modal">Abbruch</button>
				</div>
			</div>
		</div>
	</div>

	<!-- modal reset-confirmation window -->
	<div class="modal fade" id="resetConfirmationModal" role="dialog">
		<div class="modal-dialog" role="document">
			<div class="modal-content">
				<!-- modal header -->
				<div class="modal-header bg-warning">
					<h4 class="modal-title">Achtung</h4>
				</div>
				<!-- modal body -->
				<div class="modal-body text-center">
					<p>
						Sollen die Änderungen wirklich zurückgesetzt werden?
					</p>
				</div>
				<!-- modal footer -->
				<div class="modal-footer d-flex justify-content-center">
					<button type="button" class="btn btn-success" data-dismiss="modal" @click="resetValues">Fortfahren</button>
					<button type="button" class="btn btn-danger" data-dismiss="modal">Abbruch</button>
				</div>
			</div>
		</div>
	</div>

	<!-- modal not-valid-confirmation window -->
	<div class="modal fade" id="formNotValidModal" role="dialog">
		<div class="modal-dialog" role="document">
			<div class="modal-content">
				<!-- modal header -->
				<div class="modal-header bg-danger">
					<h4 class="modal-title text-light">Fehler</h4>
				</div>
				<!-- modal body -->
				<div class="modal-body text-center">
					<p>
						Es wurden fehlerhafte Eingaben gefunden, speichern ist nicht möglich! Bitte überprüfen Sie alle Eingaben.
					</p>
				</div>
				<!-- modal footer -->
				<div class="modal-footer d-flex justify-content-center">
					<button type="button" class="btn btn-primary" data-dismiss="modal">Schließen</button>
				</div>
			</div>
		</div>
	</div>

	<!-- modal no-values-changed window -->
	<div class="modal fade" id="noValuesChangedInfoModal" role="dialog">
		<div class="modal-dialog" role="document">
			<div class="modal-content">
				<!-- modal header -->
				<div class="modal-header bg-info">
					<h4 class="modal-title text-light">Info</h4>
				</div>
				<!-- modal body -->
				<div class="modal-body text-center">
					<p>
						Es wurden keine geänderten Einstellungen gefunden.
					</p>
				</div>
				<!-- modal footer -->
				<div class="modal-footer d-flex justify-content-center">
					<button type="button" class="btn btn-success" data-dismiss="modal">Ok</button>
				</div>
			</div>
		</div>
	</div>
	<!-- <<< end of common modal dialogues -->

	<div id="nav"></div> <!-- placeholder for navbar -->

	<div role="main" class="container">
		<div id="content">
			<h1>{{ title }}</h1>
			<form id="myForm">
				<slot></slot>
				<submit-buttons></submit-buttons>
			</form>
		</div>
		<donation-banner></donation-banner>
	</div>  <!-- main container -->

	<page-footer :location='footer'></page-footer>
</script>

<!-- vue apps start here -->
<script>
	const textInputComponent = {
		name: "TextInput",
		template: '#text-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: { type: [String, Object] },
			subtype: { validator: function(value){
				return ['text', 'email', 'host', 'url', 'user', 'json', 'password'].indexOf(value) !== -1;
				}, default: 'text'
			},
			pattern: String
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false,
				showPassword: false
			}
		},
		computed: {
			value: {
				get() {
					if(this.subtype == 'json'){
						return JSON.stringify(this.modelValue);
					}
					return this.modelValue;
				},
				set(newValue) {
					if(this.subtype == 'json'){
						this.$emit('update:modelValue', JSON.parse(newValue));
					} else {
						this.$emit('update:modelValue', newValue);
					}
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			},
			togglePassword() {
				this.showPassword = !this.showPassword;
			}
		}
	};

	const numberInputComponent = {
		name: "NumberInput",
		template: '#number-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: { type: Number },
			unit: String,
			min: Number,
			max: Number,
			step: Number
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false
			}
		},
		computed: {
			value: {
				get(){
					return this.modelValue;
				},
				set(newValue){
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		}
	};

	const rangeInputComponent = {
		name: "RangeInput",
		template: '#range-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: { type: Number },
			unit: String,
			min: { type: Number, default: 0 },
			max: { type: Number, default: 100 },
			step: { type: Number, default: 1 },
			labels: { type: Array, default: undefined },
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false
			}
		},
		computed: {
			label() {
				currentLabel = '';
				if(this.labels){
					if(this.sliderValue < this.labels.length){
						currentLabel = this.labels[this.sliderValue].label;
					} else {
						console.error('index out of bounds: '+this.sliderValue);
					}
				} else {
					currentLabel = this.sliderValue;
				}
				if(typeof currentLabel == 'number' && this.unit){
					currentLabel += ' ' + this.unit;
				}
				return currentLabel;
			},
			sliderValue: {
				get() {
					if(this.labels){
						var myValue = undefined;
						for(index = 0; index < this.labels.length; index++){
							if(this.labels[index].value == this.modelValue){
								myValue = index;
								break;
							}
						}
						if(myValue === undefined){
							console.warn("sliderValue: not found in values: "+this.modelValue);
						} else {
							return myValue;
						}
					}
					return this.modelValue;
				},
				set(newSliderValue){
					if(this.labels){
						var myValue = this.labels[newSliderValue].value
						// console.log("set sliderValue: "+newSliderValue+" -> "+myValue);
						this.$emit('update:modelValue', myValue);
					} else {
						this.$emit('update:modelValue', newSliderValue);
					}
				}
			},
			value: {
				get() {
					return this.modelValue;
				},
				set(newValue) {
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			},
			increment() {
				this.sliderValue = Math.min(this.sliderValue+this.step, this.max);
			},
			decrement() {
				this.sliderValue = Math.max(this.sliderValue-this.step, this.min);
			}
		}
	};

	const textareaInputComponent = {
		name: "TextareaInput",
		template: '#textarea-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: String
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false
			}
		},
		computed: {
			value: {
				get() {
					return this.modelValue;
				},
				set(newValue) {
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		}
	};

	const selectInputComponent = {
		name: "SelectInput",
		template: '#select-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: { type: [String, Number, Array] },
			groups: Object,
			options: Object
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false
			}
		},
		computed: {
			value: {
				get() {
					return this.modelValue;
				},
				set(newValue) {
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		// beforeMount(){
		// 	debug("beforeMount: "+this.title);
		// 	this.setToggleSelector(this.value);
		// },
		// mounted() {
		// 	console.debug("mounted: "+this.title);
		// },
		// beforeUpdate() {
		// 	console.debug("beforeUpdate: "+this.title);
		// },
		// updated() {
		// 	console.debug("updated: "+this.title);
		// },
		// beforeUnmount() {
		// 	console.debug("beforeUnmount: "+this.title);
		// },
		// unmounted() {
		// 	console.debug("unmounted: "+this.title);
		// },
		// errorCaptured() {
		// 	console.error("errorCaptured: "+this.title);
		// },
		// renderTracked() {
		// 	console.debug("renderTracked: "+this.title);
		// },
		// renderTriggered() {
		// 	console.debug("renderTriggered: "+this.title);
		// },
		// activated() {
		// 	console.debug("activated: "+this.title);
		// },
		// deactivated() {
		// 	console.debug("deactivated: "+this.title);
		// }
	};

	const buttongroupInputComponent = {
		name: "ButtonGroupInput",
		template: '#buttongroup-input-template',
		props: {
			title: String,
			modelValue: { type: [String, Number, Boolean] },
			buttons: Object
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false
			}
		},
		computed: {
			value: {
				get() {
					return this.modelValue;
				},
				set(newValue) {
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		// beforeMount(){
		// 	// console.debug("beforeMount: "+this.title);
		// 	this.setToggleSelector(this.value);
		// },
		// mounted() {
		// 	console.debug("mounted: "+this.title);
		// },
		// beforeUpdate() {
		// 	console.debug("beforeUpdate: "+this.title);
		// },
		// updated() {
		// 	console.debug("updated: "+this.title);
		// },
		// beforeUnmount() {
		// 	console.debug("beforeUnmount: "+this.title);
		// },
		// unmounted() {
		// 	console.debug("unmounted: "+this.title);
		// },
		// errorCaptured() {
		// 	console.error("errorCaptured: "+this.title);
		// },
		// renderTracked() {
		// 	console.debug("renderTracked: "+this.title);
		// },
		// renderTriggered() {
		// 	console.debug("renderTriggered: "+this.title);
		// },
		// activated() {
		// 	console.debug("activated: "+this.title);
		// },
		// deactivated() {
		// 	console.debug("deactivated: "+this.title);
		// }
	};

	const checkboxInputComponent = {
		name: "CheckboxInput",
		template: '#checkbox-input-template',
		inheritAttrs: false,
		props: {
			title: String,
			modelValue: { type: Boolean },
		},
		emits: [
			'update:modelValue'
		],
		data() {
			return {
				showHelp: false,
			}
		},
		computed: {
			value: {
				get() {
					return this.modelValue;
				},
				set(newValue) {
					this.$emit('update:modelValue', newValue);
				}
			}
		},
		methods: {
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		// beforeMount(){
		// 	// console.debug("beforeMount: "+this.title);
		// 	this.setToggleSelector(this.value);
		// },
		// mounted() {
		// 	console.debug("mounted: "+this.title);
		// },
		// beforeUpdate() {
		// 	console.debug("beforeUpdate: "+this.title);
		// },
		// updated() {
		// 	console.debug("updated: "+this.title);
		// },
		// beforeUnmount() {
		// 	console.debug("beforeUnmount: "+this.title);
		// },
		// unmounted() {
		// 	console.debug("unmounted: "+this.title);
		// },
		// errorCaptured() {
		// 	console.error("errorCaptured: "+this.title);
		// },
		// renderTracked() {
		// 	console.debug("renderTracked: "+this.title);
		// },
		// renderTriggered() {
		// 	console.debug("renderTriggered: "+this.title);
		// },
		// activated() {
		// 	console.debug("activated: "+this.title);
		// },
		// deactivated() {
		// 	console.debug("deactivated: "+this.title);
		// }
	};

	const alertComponent = {
		name: "Alert",
		template: '#alert-template',
		props: {
			subtype: { validator: function(value){
				return ['info', 'success', 'warning', 'danger', 'primary', 'secondary', 'light', 'dark'].indexOf(value) !== -1;
				}, default: 'secondary'
			}
		}
	};

	const headingComponent = {
		name: "Heading",
		template: '#heading-template'
	};

	const submitButtonsComponent = {
		name: "SubmitButtons",
		template: '#submit-buttons-template',
		methods: {
			saveSettings() {
				this.$root.saveSettings();
			},
			showResetModal() {
				this.$root.showResetModal();
			},
			showDefaultsModal() {
				this.$root.showDefaultsModal();
			}
		}
	}

	const cardComponent = {
		name: 'Card',
		template: "#card-template",
		props: {
			title: { type: String, default: "# no title set #" },
			subtype: { validator: function(value){
				return ['info', 'success', 'warning', 'danger', 'primary', 'secondary', 'light', 'dark'].indexOf(value) !== -1;
				}, default: 'secondary'
			}
		}
	}

	const pageFooterComponent = {
		name: "PageFooter",
		template: "#page-footer-template",
		props: {
			location: { type: String, default: "# no location set #" }
		}
	}

	const donationBannerComponent = {
		name: "DonationBanner",
		template: '#donation-banner-template'
	}

	const contentComponent = {
		name: "content",
		template: "#content-template",
		props: {
			title: { type: String, default: "# no title set #" },
			footer: { type: String, default: "# no footer set #" },
			nav: String
		},
		components: {
			'submit-buttons': submitButtonsComponent,
			'page-footer': pageFooterComponent,
			'donation-banner': donationBannerComponent
		},
		methods: {
			resetValues() {
				this.$root.resetValues();
			},
			setDefaultValues() {
				this.$root.setDefaultValues();
			}
		},
		beforeMount(){
			// old jquery code
			// ToDo: add nav component
			const navElement = this.nav;
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$(navElement).addClass('disabled');
				}
			);
		}
	}

	const contentApp = {
		name: "contentApp",
		data() {
			return {
				// title: document.getElementById('app').dataset.title,
				// footer: document.getElementById('app').dataset.footer,
				client: undefined,
				clientOptions: {
					timeout: 5,
					useSSL: location.protocol == 'https:',
					// Gets Called if the connection has sucessfully been established
					onSuccess: this.onClientSuccess,
					// Gets Called if the connection could not be established
					onFailure: this.onClientFailure
				},
				topicsToSubscribe: [],
				// will store all visibility options from components
				visibility: {},
				// copy default values
				componentData: JSON.parse(JSON.stringify(componentDefaultData)),
				componentInitialData : JSON.parse(JSON.stringify(componentDefaultData))
			}
		},
		components: {
			'text-input': textInputComponent,
			'textarea-input': textareaInputComponent,
			'number-input': numberInputComponent,
			'range-input': rangeInputComponent,
			'select-input': selectInputComponent,
			'buttongroup-input': buttongroupInputComponent,
			'checkbox-input': checkboxInputComponent,
			'alert': alertComponent,
			'heading': headingComponent,
			'card': cardComponent,
			'content': contentComponent
		},
		methods: {
			showResetModal() {
				$('#resetConfirmationModal').modal();
			},
			resetValues() {
				console.info("discarding changes...");
				this.componentData = JSON.parse(JSON.stringify(this.componentInitialData));
			},
			showDefaultsModal() {
				$('#setDefaultsConfirmationModal').modal();
			},
			setDefaultValues() {
				console.info("setting defaults...");
				this.componentData = JSON.parse(JSON.stringify(componentDefaultData));
			},
			saveSettings() {
				// sends all changed values by mqtt if valid
				var formValid = $("#myForm")[0].checkValidity();
				console.info("validity: "+formValid);
				if ( !formValid ) {
					$('#formNotValidModal').modal();
					return;
				};
				this.getChangedValues();
				this.sendValues();
			},
			getChangedValues() {
				for (element in this.componentData) {
					// console.debug("checking: " + element);
					initialValue = JSON.stringify(this.componentInitialData[element]);
					currentValue = JSON.stringify(this.componentData[element]);
					// console.debug("initial value: " + initialValue);
					// console.debug("current value: " + currentValue);
					if (initialValue != currentValue) {
						console.debug("value ist changed: "+element);
						var message = JSON.stringify(this.componentData[element]);
						var topic = element.replace(/^openWB\//, 'openWB/set/');
						changedValues[topic] = message;
					}
				}
			},
			checkAllSaved(topic, value) {
				/** @function checkAllSaved
				 * checks if received value equals the last saved and removes key from array
				 * @param {string} topic - the complete mqtt topic
				 * @param {string} value - the value for the topic
				 * @requires global var:changedValues - is declared with proxy in helperFunctions.js
				 */
				topic = topic.replace('openWB/', 'openWB/set/');
				console.debug("checkAllSaved: "+topic);
				if (changedValues.hasOwnProperty(topic) && changedValues[topic] == value) {
					// received topic-value-pair equals one that was send before
					delete changedValues[topic]; // delete it
					// proxy will initiate redirect to main page if array is now empty
				}
			},
			sendValues() {
				if (!(Object.keys(changedValues).length === 0)) {
					// there are changed values
					// so first show saveprogress on page
					$('#saveprogress').removeClass('hide');
					// delay in ms between publishes
					var intervall = 200;
					// then send changed values
					publish = this.publish;
					Object.keys(changedValues).forEach(function(topic, index) {
						var value = this[topic];
						setTimeout(function() {
							console.debug("publishing changed value: " + topic + ": " + value);
							// as all empty messages are not processed by mqttsub.py, we have to send something usefull
							if (value.length == 0) {
								publish("none", topic);
								// delete empty values as we will never get an answer
								console.debug("deleting empty changedValue: " + topic)
								delete changedValues[topic];
							} else {
								publish(value, topic);
							}
						}, index * intervall);
					}, changedValues);

				} else {
					$('#noValuesChangedInfoModal').modal();
				}
			},
			publish(payload, topic) {
				var message = new Messaging.Message(payload);
				message.destinationName = topic;
				message.qos = 2;
				message.retained = true;
				// this.client.send(message);
				console.info("publishing disabled!");
				console.debug("sent: "+topic+": "+payload);
			},
			addTopicToSubscribe(topic) {
				if(this.topicsToSubscribe.indexOf(topic) == -1) {
					this.topicsToSubscribe.push(topic);
				} else {
					console.warn("duplicate topic to subscribe: "+topic);
				}
			},
			removeTopicToSubscribe(topic) {
				var index = this.topicsToSubscribe.indexOf(topic);
				if(index != -1) {
					this.topicsToSubscribe.splice(index, 1);
				} else {
					console.warn("unknown topic to remove: "+topic);
				}
			},
			onClientSuccess() {
				this.topicsToSubscribe.forEach((topic) => {
					console.debug("subscribing: "+topic);
					this.client.subscribe(topic, {qos: 0});
				});
			},
			onClientFailure() {
				console.warn("client failure! reconnecting...");
				this.client.connect(this.options);
			},
			onClientConnectionLost() {
				console.warn("client connection lost! reconnecting...");
				this.client.connect(this.options);
			},
			onClientMessageArrived(message) {
				//Gets called whenever you receive a message
				console.info("message received: "+message.destinationName+": "+message.payloadString);
				this.checkAllSaved(message.destinationName, message.payloadString);
				if (message.destinationName in this.componentData) {
					if (message.payloadString.length) {
						this.componentData[message.destinationName] = JSON.parse(message.payloadString);
					} else {
						// restore default value if empty message received
						console.info("restoring defauult value: "+JSON.stringify(componentDefaultData[message.destinationName]));
						this.componentData[message.destinationName] = JSON.parse(JSON.stringify(componentDefaultData[message.destinationName]));
					}
					// update initial data
					this.componentInitialData[message.destinationName] = JSON.parse(JSON.stringify(this.componentData[message.destinationName]));
				} else {
					console.warn("no data found: " + message.destinationName);
				}
			}
		},
		beforeMount(){
			// setup mqtt client
			var clientuid = Math.random().toString(36).replace(/[^a-z]+/g, "").substr(0, 5);
			this.client = new Messaging.Client(location.hostname, 9001, clientuid);
			// setup handlers
			this.client.onConnectionLost = this.onClientConnectionLost;
			this.client.onDeliveryComplete = this.onClientDeliveryComplete;
			this.client.onMessageArrived = this.onClientMessageArrived;
		},
		mounted() {
			// collect topict to subscribe
			for (topic in this.componentData) {
				console.debug("adding topic: "+topic);
				this.addTopicToSubscribe(topic);
			};
			// connect to broker
			this.client.connect(this.clientOptions);
		},
		// beforeUpdate() {
		// 	console.debug("onBeforeUpdate");
		// },
		// updated() {
		// 	console.debug("onUpdated");
		// },
		// beforeUnmount() {
		// 	console.debug("onBeforeUnmount");
		// },
		// unmounted() {
		// 	console.debug("onUnmounted");
		// },
		// errorCaptured() {
		// 	console.error("onErrorCaptured");
		// },
		// renderTracked() {
		// 	console.debug("onRenderTracked");
		// },
		// renderTriggered() {
		// 	console.debug("onRenderTriggered");
		// },
		// activated() {
		// 	console.debug("onActivated");
		// },
		// deactivated() {
		// 	console.debug("onDeactivated");
		// }
	}

	const vApp = Vue.createApp(contentApp).mount('#app');
</script>
