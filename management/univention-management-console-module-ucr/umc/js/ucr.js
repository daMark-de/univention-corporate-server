/*
 * Copyright 2011-2017 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/aspect",
	"dojo/sniff",
	"dojo/on",
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/Dialog",
	"dijit/form/_TextBoxMixin",
	"umc/store",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"umc/widgets/Grid",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/StandbyMixin",
	"umc/widgets/SearchBox",
	"umc/widgets/TextBox",
	"umc/widgets/Text",
	"umc/widgets/HiddenInput",
	"umc/widgets/ComboBox",
	"umc/widgets/Tooltip",
	"umc/widgets/Button",
	"umc/widgets/ContainerWidget",
	"put-selector/put",
	"umc/i18n!umc/modules/ucr",
	"xstyle/css!./ucr.css"
], function(declare, lang, kernel, array, aspect, has, on, domClass, entities, Dialog, _TextBoxMixin, umcStore, tools, dialog, Form, Grid, Module, Page, SearchForm, StandbyMixin, SearchBox, TextBox, Text, HiddenInput, ComboBox, Tooltip, Button, ContainerWidget, put, _) {

	var MyValueField = declare([ContainerWidget], {
		'class': 'valueField',
		buildRendering: function() {
			this.inherited(arguments);
			var textbox = new TextBox({
				value: this.value
			});
			put(textbox.domNode.firstChild, '- div.savingContainer div.border + div.tick div.left + div.right');
			this.addChild(textbox);
			this.textbox = textbox;
			this.initialValue = this.value;
			var revertButton = put(this.domNode, 'div.revertButton.dijitDisplayNone');
			this.revertButton = revertButton;
			on(revertButton, 'click', lang.hitch(this, function() {
				this.onRevert(this.item, this);
			}));
		},

		onRevert: function(item, valueField) {
			// stub
		}
	});

	var _DetailDialog = declare([Dialog, StandbyMixin], {
		_form: null,
		_description: null,
		moduleStore: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				_locale: kernel.locale.substr(0, 2),
				'class': 'umcUcrDialog',
				title: _('Edit UCR variable')
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: TextBox,
				name: 'key',
				description: _( 'Name of UCR variable' ),
				label: _( 'UCR variable' )
			}, {
				type: TextBox,
				name: 'value',
				description: _( 'Value of the UCR variable' ),
				label: _( 'Value' )
			}, {
				type: Text,
				name: 'description',
				description: _( 'Description of the UCR variable' ),
				label: _( 'Description:' ),
//				style: 'margin-bottom: 5px'
			}, {
				type: HiddenInput,
				name: 'description[' + this._locale + ']'
	//		}, {
	//			type: 'MultiSelect',
	//			name: 'categories',
	//			description: _( 'Categories that the UCR variable is associated with' ),
	//			label: _( 'Categories' ),
	//			dynamicValues: 'ucr/categories'
			}];

			var buttons = [{
				//FIXME: Should be much simpler. The key name should be enough
				name: 'cancel',
				label: _( 'Cancel' ),
				callback: lang.hitch(this, function() {
					this.hide();
				})
			}, {
				name: 'submit',
				label: _( 'Save' ),
				callback: lang.hitch(this, function() {
					this._form.save();
				})
			}];

			var layout = ['key', 'value', 'description'];//, ['categories']];

			this._form = this.own(new Form({
				widgets: widgets,
				buttons: buttons,
				layout: layout,
				moduleStore: this.moduleStore,
				cols: 1
			}))[0];
			this._form.placeAt(this.containerNode);

			// simple handler to disable standby mode
			this._form.on('loaded', lang.hitch(this, function() {
				// display the description text
				var descWidget = this._form.getWidget('description');
				var text = this._form.getWidget('description[' + this._locale + ']').get('value');
				if (text) {
					// we have description, update the description field
					descWidget.set('visible', true);
					descWidget.set('content', '<i>' + entities.encode(text) + '</i>');
				}
				else {
					// no description -> hide widget and label
					descWidget.set('visible', false);
					descWidget.set('content', '');
				}

				// disable the loading animation
				this._position();
				this.standby(false);
			}));
			this._form.on('saved', lang.hitch(this, function(success) {
				if (success) {
					this.hide();
				}
				this._position();
				this.standby(false);
			}));
		},

		clearForm: function() {
			var emptyValues = {};
			this._form.getWidget('key').setValid(true);
			this._form.getWidget('value').setValid(true);
			tools.forIn(this._form.get('value'), function(ikey) {
				emptyValues[ikey] = '';
			});
			this._form.setFormValues(emptyValues);
			var descWidget = this._form.getWidget('description');
			descWidget.set('content', '');
			descWidget.set('visible', false);
			this._position();
		},

		newVariable: function(item) {
			this.set('title', _('Add UCR variable'));
			this._form._widgets.key.set('disabled', false);
			this.clearForm();
			if (item) {
				this._form._widgets.key.set('value', item.key);
				this._form._widgets.description.set('visible', true);
				this._form._widgets.description.set('content', item.description);
			}
			this.standby(false);
			this.show();
		},

		loadVariable: function(ucrVariable) {
			this.set('title', _('Edit UCR variable'));
			this._form._widgets.key.set('disabled', true);

			this.standby(true);
			this.show();

			// clear form and start the query
			this.clearForm();
			this._form.load(ucrVariable);
		},

		getValues: function() {
			// description:
			//		Collect a property map of all currently entered/selected values.

			return this._form.get('value');
		},

		onSubmit: function(values) {
			// stub for event handling
		}
	});

	return declare("umc.modules.ucr", Module, {
		// summary:
		//		Module for modifying and displaying UCR variables on the system.

		_grid: null,
		_store: null,
		_searchForm: null,
		_detailDialog: null,
		_contextVariable: null,
		_page: null,

		moduleID: 'ucr',
		idProperty: 'key',

		changes: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.changes = {};
			// TODO is 'flavor' important
			this.eventlessStore = umcStore(this.idProperty, this.moduleID, 'myflavor');
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				helpText: _('The Univention Configuration Registry (UCR) is the local database for the configuration of UCS systems to access and edit system-wide properties in a unified manner. Caution: Changing UCR variables directly results in the change of the system configuration. Misconfiguration may cause an unusable system!'),
				fullWidth: true
			});
			this.addChild(this._page);

			var actions = [{
				name: 'add',
				label: _( 'Add' ),
				description: _( 'Adding a new UCR variable' ),
				iconClass: 'umcIconAdd',
				isContextAction: false,
				isStandardAction: true,
				callback: lang.hitch(this, function() {
					this._detailDialog.newVariable();
				})
			}, {
				name: 'edit',
				label: _( 'Edit' ),
				description: _( 'Setting the UCR variable, editing the categories and/or description' ),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, '_edit')
			}, {
				name: 'delete',
				label: _( 'Delete' ),
				description: _( 'Deleting the selected UCR variables' ),
				iconClass: 'umcIconDelete',
				isStandardAction: true,
				isMultiAction: true,
				canExecute: function(item) {
					return !item.isTemplate
				},
				callback: lang.hitch(this, function(ids) {
					dialog.confirm(_('Are you sure to delete the %d selected UCR variable(s)?', ids.length), [{
						label: _('Cancel'),
						'default': true
					}, {
						label: _('Delete'),
						callback: lang.hitch(this, function() {
							// remove the selected elements via a transaction on the module store
							var transaction = this.moduleStore.transaction();
							array.forEach(ids, lang.hitch(this.moduleStore, 'remove'));
							transaction.commit();
						})
					}]);

				})
			}];

			// define grid columns
			var columns = [{
				name: 'key',
				label: _( 'UCR variable' ),
				description: _( 'Unique name of the UCR variable' ),
				formatter: lang.hitch(this, '_keyFormatter')
			}, {
				name: 'value',
				label: _( 'Value' ),
				description: _( 'Value of the UCR variable' ),
				formatter: lang.hitch(this, '_valueFormatter')
			}];

			// generate the data grid
			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				query: {
					category: "all",
					key: "all",
					pattern: "*"
				}
			});

			var widgets = [{
				type: ComboBox,
				name: 'category',
				value: 'all',
				description: _( 'Category the UCR variable should be associated with' ),
				label: _('Category'),
				staticValues: [
					{ id: 'all', label: _('All') }
				],
				dynamicValues: 'ucr/categories',
				size: 'Half'
			}, {
				type: ComboBox,
				name: 'key',
				value: 'all',
				description: _( 'Select the attribute of a UCR variable that should be searched for the given keyword' ),
				label: _( 'Search attribute' ),
				staticValues: [
					{ id: 'all', label: _( 'All' ) },
					{ id: 'key', label: _( 'Variable' ) },
					{ id: 'value', label: _( 'Value' ) },
					{ id: 'description', label: _( 'Description' ) }
				],
				size: 'Half'
			}, {
				type: SearchBox,
				name: 'pattern',
				value: '*',
				inlineLabel: _('Search...'),
				onSearch: lang.hitch(this, function() {
					this._searchForm.submit();
				})
			}];

			this._searchForm = new SearchForm({
				region: 'nav',
				hideSubmitButton: true,
				widgets: widgets,
				layout: [[ 'category', 'key', 'pattern' ]]
			});
			this._searchForm.on('search', lang.hitch(this._grid, 'filter'));

			this._page.addChild(this._searchForm);
			this._page.addChild(this._grid);
			this._page.startup();

			// Do not focus on touch devices (e.g. tablets)
			if (!has('touch')) {
				// make sure that the input field is focused
				this.own(aspect.after(this._page, '_onShow', lang.hitch(this, '_selectInputText')));
				this._grid.on('filterDone', lang.hitch(this, '_selectInputText'));
			}

			this._detailDialog = new _DetailDialog({
				moduleStore: this.moduleStore
			});
			this.own(this._detailDialog);
			this._detailDialog.startup();
		},

		_edit: function(ids, items) {
			if (items[0].isTemplate) {
				// TODO no check for multiedit yet
				this._detailDialog.newVariable({
					key: ids[0].replace(/\.\*/g, _('<your value>')),
					description: items[0].description || ''
				});
			} else if (ids.length) {
				this._detailDialog.loadVariable(ids[0]);
			}
		},

		_selectInputText: function() {
			// focus on input widget
			var widget = this._searchForm.getWidget('pattern');
			widget.focus();

			// select the text
			if (widget.textbox) {
				try {
					_TextBoxMixin.selectInputText(widget.textbox);
				}
				catch(err) { }
			}
		},

		_keyFormatter: function(label, item) {
			var widget = new Text({
				content: label
			});
			this.own(widget);

			var item = this._grid.getRowValues(item);
			if (item.description) {
				var tooltip = new Tooltip({
					label: entities.encode(item.description),
					connectId: [widget.domNode],
					position: ['below', 'above']
				});
				widget.own(tooltip);
			}
			return widget;
		},

		_valueFormatter: function(label, item) {
			var ret;
			if (item.isTemplate) {
				ret = new Text({
					content: _('Create variable'),
					'class': 'templateText'
				});
				on(ret, 'click', lang.hitch(this, '_edit', [item.key], [item]));
			} else {
				ret =  MyValueField({
					value: label,
					item: item
				});
				on(ret, 'revert', lang.hitch(this, '_revert'));
				var _item = this._grid.getRowValues(item);
				if (_item.description) {
					var tooltip = new Tooltip({
						label: entities.encode(_item.description),
						position: ['below', 'above']
					});
					ret.own(tooltip);
				}
				on(ret.textbox, 'focus', lang.hitch(this, function() {
					tooltip.set('connectId', [ret.domNode]);
				}));
				on(ret.textbox, 'blur', lang.hitch(this, function() {
					tooltip.set('connectId', []);
				}));
				on(ret, 'keydown', lang.hitch(this, function(evt) {
					if (evt.key === 'Enter' || evt.key === 'Tab') {
						if (evt.target.value === ret.initialValue || !ret.initialValue && evt.target.value === '') {
							// TODO remove
							console.log('noChange');
							return;
						}
						this._inPlaceSave(item, evt.target.value, ret, true);
					}
				}));
			}

			return ret;
		},

		_inPlaceSave: function(item, newValue, valueField, addToHistory) {
			domClass.add(valueField.domNode, 'shown');
			valueField.textbox.set('disabled', true);

			// have the loading animation play for at least 800ms
			// so there are no quick animation switches
			var defer = tools.defer(function() {}, 800);
			setTimeout(function() {
				domClass.add(valueField.domNode, 'saving');
			}, 10);
			var deferred = this._inPlaceEdit(item, newValue, addToHistory);
			deferred.then(lang.hitch(this, function() {
				valueField.initialValue = newValue;
				defer.then(lang.hitch(this, function() {
					domClass.remove(valueField.domNode, 'saving');
					domClass.add(valueField.domNode, 'saved');
					setTimeout(lang.hitch(this, function() {
						domClass.remove(valueField.domNode, 'saved');
						domClass.remove(valueField.domNode, 'shown');
						valueField.textbox.set('disabled', false);
						if (this.changes[item.key]) {
							domClass.remove(valueField.revertButton, 'dijitDisplayNone');
						} else {
							domClass.add(valueField.revertButton, 'dijitDisplayNone');
						}
						// valueField.textbox.focus();
					}), 1550);
				}));
			}));
			return deferred;
		},

		_inPlaceEdit: function(item, newValue, addToHistory) {
			var oldValue = item.value;
			item.value = newValue;
			// this.moduleStore._noEvents = true;
			var options = {};
			var idProperty = lang.getObject('moduleStore.idProperty', false, this);
			if (idProperty) {
				options[idProperty] = item.key;
			}
			deferred = this.eventlessStore.put(item, options, false);
			deferred.then(lang.hitch(this, function() {
				if (addToHistory) {
					if (!this.changes[item.key]) {
						this.changes[item.key] = [];
					}
					this.changes[item.key].push(oldValue);
				}
				this._grid.update();
				// this.moduleStore._noEvents = false;
			}), lang.hitch(this, function() {
				// TODO error case
				console.log('saving ucr variable failed');
			}));

			return deferred;
		},

		_revert: function(item, valueField) {
			var value = this.changes[item.key].pop();
			valueField.textbox.set('value', value);
			this._inPlaceSave(item, value, valueField, false).then(lang.hitch(this, function() {
				if (this.changes[item.key].length === 0) {
					delete this.changes[item.key];
				}
			}));
		}
	});
});
