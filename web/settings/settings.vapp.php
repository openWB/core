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
				<button type="button" class="btn btn-success" data-dismiss="modal" id="saveDefaultsBtn">Fortfahren</button>
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
				<button type="button" class="btn btn-success" data-dismiss="modal" id="resetBtn">Fortfahren</button>
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

<!-- old JQuery code TODO -->
<script>
	$(function() {
		$('#resetBtn').on('click',function() {
			vApp.resetValues();
		});

		$('#saveDefaultsBtn').on("click",function() {
			vApp.setDefaultValues();
		});
	});
</script>

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
					<div v-if="subtype != 'text'" class="input-group-prepend">
						<div class="input-group-text">
							<i v-if="subtype == 'email'" class="fa fa-fw fa-envelope"></i>
							<i v-if="subtype == 'host'" class="fas fa-fw fa-network-wired"></i>
							<i v-if="subtype == 'url'" class="fas fa-fw fa-globe"></i>
							<i v-if="subtype == 'user'" class="fa fa-fw fa-user"></i>
						</div>
					</div>
					<input v-if="['text', 'user'].includes(subtype)" type="text" class="form-control" v-model="value" :disabled="disabled" :pattern="pattern">
					<input v-if="subtype === 'host'" type="text" class="form-control" v-model="value" :disabled="disabled" pattern="^(((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])|[A-Za-z0-9\._\-]*)$">
					<input v-if="['email', 'url'].includes(subtype)" :type="subtype" class="form-control" v-model="value" :disabled="disabled">
				</div>
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="password-input-template">
	<div class="form-row mb-1">
		<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
			{{ title }}
			<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
		</label>
		<div class="col-md-8">
			<div class="form-row">
				<div class="input-group">
					<div class="input-group-prepend" v-on:click="togglePassword">
						<div class="input-group-text">
							<i class="fa fa-fw" :class="showPassword ? 'fa-unlock' : 'fa-lock'"></i>
						</div>
					</div>
					<input :type="showPassword ? 'text' : 'password'" class="form-control" v-model="value" :disabled="disabled" :pattern="pattern">
					<div class="input-group-append" v-on:click="togglePassword">
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
					<input type="number" class="form-control" :min="min" :max="max" :step="step" v-model.number="value" :disabled="disabled">
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
					<input type="range" class="form-control-range rangeInput" :min="min" :max="max" :step="step" v-model.number="value" :disabled="disabled">
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
				<textarea class="form-control" :disabled="disabled">{{ value }}</textarea>
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
				<select class="form-control" v-model="value" :disabled="disabled">
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
					<label v-for="button in buttons" class="btn" :class="[ value == button.buttonValue ? 'active' : '', button.class ? button.class : 'btn-outline-info', disabled ? 'disabled' : '' ]">
						<input type="radio" v-model="value" :value="button.buttonValue" :disabled="disabled">{{ button.text }}
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
				<input class="form-control" type="checkbox" v-model="value" :disabled="disabled">
			</div>
			<span v-if="showHelp" class="form-row alert alert-info my-1 small">
				<slot name="help"></slot>
			</span>
		</div>
	</div>
</script>

<script type="text/x-template" id="alert-template">
	<div class="card-text alert" :class="'alert-'+subtype">
		<slot name="message"></slot>
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
	<div class="card border-secondary">
		<div class="card-header bg-secondary">
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
	<!-- Saveprogress -->
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
		props: {
			title: String,
			defaultValue: { type: String, default: "" },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			subtype: { validator: function(value){
				return ['text', 'email', 'host', 'url', 'user'].indexOf(value) !== -1;
				}, default: 'text'
			},
			pattern: String
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			}
		},
		methods: {
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		}
	};

	const passwordInputComponent = {
		name: "PasswordInput",
		template: '#password-input-template',
		props: {
			title: String,
			defaultValue: { type: String, default: "" },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			pattern: String
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false,
				showPassword: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			}
		},
		methods: {
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
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
		props: {
			title: String,
			defaultValue: { type: Number, default: 0 },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			unit: String,
			min: Number,
			max: Number,
			step: Number
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			}
		},
		methods: {
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		}
	};

	const rangeInputComponent = {
		name: "RangeInput",
		template: '#range-input-template',
		props: {
			title: String,
			defaultValue: { type: Number, default: 0 },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			unit: String,
			min: { type: Number, default: 0 },
			max: { type: Number, default: 100 },
			step: { type: Number, default: 1 },
			labels: { type: Array },
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			label() {
				currentLabel = '';
				if(this.labels){
					currentLabel = this.labels[this.value].label;
				} else {
					currentLabel = this.value;
				}
				if(typeof currentLabel == 'number' && this.unit){
					currentLabel += ' ' + this.unit;
				}
				return currentLabel;
			},
			mqttValue: {
				get() {
					if(this.labels){
						return this.labels[this.value].value;
					}
					return this.value;
				},
				set(newMqttValue) {
					if(this.labels){
						var newValue = undefined;
						for(index = 0; index < this.labels.length; index++){
							if(this.labels[index].value == newMqttValue){
								newValue = index;
								break;
							}
						}
						if(newValue === undefined){
							console.warn("mqttValue: not found in values: "+newMqttValue);
						} else {
							this.value = newValue;
							this.initialValue = newValue;
						}
					} else {
						this.value = newMqttValue;
						this.initialValue = newMqttValue;
					}
				}
			}
		},
		watch: {
			value(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			}
		},
		methods: {
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			},
			increment() {
				this.value = Math.min(this.value+this.step, this.max);
			},
			decrement() {
				this.value = Math.max(this.value-this.step, this.min);
			}
		}
	};

	const textareaInputComponent = {
		name: "TextareaInput",
		template: '#textarea-input-template',
		props: {
			title: String,
			defaultValue: { type: String, default: "" },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			}
		},
		methods: {
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		}
	};

	const selectInputComponent = {
		name: "SelectInput",
		template: '#select-input-template',
		props: {
			title: String,
			defaultValue: { type: [String, Number, Array], default: "" },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			groups: Object,
			options: Object
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				this.setToggleSelector(newValue);
			}
		},
		methods: {
			setToggleSelector(newValue) {
				if(this.toggleSelector) {
					// console.debug('toggleSelector: '+this.toggleSelector+' newValue: '+newValue);
					let toggleSelector = this.toggleSelector;
					var done = false;
					var appData = this.$root.$data['visibility'];
					if(this.options){
						this.options.some(function(option){
							if(option.value === newValue) {
								appData[toggleSelector] = newValue;
								done = true;
								return true;
							}
						});
					}
					if(!done && this.groups){
						this.groups.some(function(group){
							return group.options.some(function(option){
								if(option.value === newValue) {
									appData[toggleSelector] = newValue;
									done = true;
									return true;
								}
							});
						});
					}
				}
			},
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		beforeMount(){
			// debug("beforeMount: "+this.title);
			this.setToggleSelector(this.value);
		},
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
			defaultValue: [String, Number, Boolean],
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String,
			buttons: Object
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				this.setToggleSelector(newValue);
			}
		},
		methods: {
			setToggleSelector(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					this.buttons.forEach(function(button){
						if(button.buttonValue === newValue) {
							appData[toggleSelector] = newValue;
						}
					});
				}
			},
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		beforeMount(){
			// console.debug("beforeMount: "+this.title);
			this.setToggleSelector(this.value);
		},
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
		props: {
			title: String,
			defaultValue: { type: Boolean, default: false },
			isDisabled: { type: Boolean, default: false },
			toggleSelector: String
		},
		data() {
			return {
				value: this.defaultValue,
				initialValue: this.defaultValue,
				showHelp: false,
			}
		},
		computed: {
			disabled() {
				return this.isDisabled;
			},
			changed() {
				return this.value != this.initialValue;
			},
			mqttValue: {
				get() {
					return this.value;
				},
				set(newMqttValue) {
					this.value = newMqttValue;
					this.initialValue = newMqttValue;
				}
			}
		},
		watch: {
			value(newValue) {
				this.setToggleSelector(newValue);
			}
		},
		methods: {
			setToggleSelector(newValue) {
				if(this.toggleSelector) {
					let toggleSelector = this.toggleSelector;
					var appData = this.$root.$data['visibility'];
					appData[toggleSelector] = newValue;
				}
			},
			setInitialValue(newDefault) {
				this.initialValue = newDefault;
			},
			setValue(newValue) {
				this.value = newValue;
			},
			resetValue() {
				this.value = this.initialValue;
			},
			setDefaultValue() {
				this.value = this.defaultValue;
			},
			toggleHelp() {
				this.showHelp = !this.showHelp && this.$slots.help;
			}
		},
		beforeMount(){
			// console.debug("beforeMount: "+this.title);
			this.setToggleSelector(this.value);
		},
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
			title: { type: String, default: "# no title set #" }
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
			footer: { type: String, default: "# no footer set #" }
		},
		components: {
			'submit-buttons': submitButtonsComponent,
			'page-footer': pageFooterComponent,
			'donation-banner': donationBannerComponent
		}
	}

	const contentApp = {
		name: "contentApp",
		// template: "#settings-app-template",
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
				visibility: {}
			}
		},
		components: {
			'text-input': textInputComponent,
			'password-input': passwordInputComponent,
			'number-input': numberInputComponent,
			'range-input': rangeInputComponent,
			'textarea-input': textareaInputComponent,
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
				console.info("resetting input elements...");
				for (element in this.$refs) {
					console.debug(element);
					this.$refs[element].resetValue();
				};
			},
			showDefaultsModal() {
				$('#setDefaultsConfirmationModal').modal();
			},
			setDefaultValues() {
				console.info("setting defaults...");
				for (element in this.$refs) {
					console.debug(element);
					this.$refs[element].setDefaultValue();
				};
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
				for (element in this.$refs) {
					// console.debug("checking: " + element);
					if (this.$refs[element].changed && !this.$refs[element].disabled) {
						console.debug("value ist changed and not disabled");
						var message = JSON.stringify(this.$refs[element].mqttValue);
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
				// console.debug("checkAllSaved: "+topic);
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
				this.client.send(message);
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
			onClientDeliveryComplete(token) {
				// func processMessages defined in respective processAllMqttMsg_
				console.debug("delivery complete: "+token);
			},
			onClientMessageArrived(message) {
				//Gets called whenever you receive a message
				console.info("message received: "+message.destinationName+": "+message.payloadString);
				this.checkAllSaved(message.destinationName, message.payloadString);
				if (message.destinationName in this.$refs) {
					if (message.payloadString.length) {
						jsonPayload = JSON.parse(message.payloadString);
						vApp.$refs[message.destinationName].mqttValue = jsonPayload;
					} else {
						// restore default value if empty message received
						vApp.$refs[message.destinationName].value = vApp.$refs[message.destinationName].defaultValue;
					}
				} else {
					console.warn("no ref found: " + message.destinationName33);
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
			for (topic in this.$refs) {
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
