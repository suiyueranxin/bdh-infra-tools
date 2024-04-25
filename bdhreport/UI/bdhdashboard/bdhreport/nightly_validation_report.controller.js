sap.ui.controller("bdhreport.nightly_validation_report", {
/**
* Called when a controller is instantiated and its View controls (if available) are already created.
* Can be used to modify the View before it is displayed, to bind event handlers and do other one-time initialization.
* @memberOf bdhreport.nightly_validation_report
*/
	showStatus:function(data) {
		var that = this;
		
		if (data == 'FAILURE') {
			return "Error";
		}else if(data == 'FINISHED') {
			return "Success";
		}else{
			return "None";
		}
	},
	
	onPressExport: function(){
		var that = this;
		var catagory = that.getView().byId("catagoryBox").getValue();		
		if (catagory==''){
        	sap.m.MessageToast.show("Please choose a catagory!");
        	return;
        }
        if (catagory == "BDH Nightly Validation") {
        	var oTable = this.getView().byId("reportTableForNightly");        	
        } 
        if (catagory == "BDH Push Validation") {
        	var oTable = this.getView().byId("reportTableForPushV");       	
        }
        if (!oTable.getModel()){
        	sap.m.MessageToast.show("There is no content in table!");
        	return;
        }
       // var oColumns = this.getColumns(oTable);
        
        var oModel = oTable.getModel();
        var dataKeys = Object.keys(oModel.oData.dataList[0]);
        var oColumns = [];       
        for (var i = 0; i < dataKeys.length; i++){
        	var column = {
        			name : dataKeys[i],
                    template : {
                        content : {
                            path : dataKeys[i]
                        }
                    }};
        	oColumns.push(column);
        }
        
		var oExport = new sap.ui.core.util.Export({
			exportType : new sap.ui.core.util.ExportTypeCSV({				
				separatorChar : ",",
	            charset : "utf-8",
			}),
			models : oModel,
			rows : {
				path : oTable.getBinding("items").getPath()
			},
			columns : oColumns
		});
		oExport.saveFile().always(function() { 
			this.destroy();                                                               
        });
	},
	
	getColumns : function(oTable) {
        var aColumns  = oTable.getColumns();
        var aItems    = oTable.getItems();
        var aTemplate = [];

        for (var i = 0; i< aColumns.length; i++) {
            var oColumn = { 
                name : aColumns[i].getHeader().getText(),
                template : {
                    content : {
                        path : null
                    }
                }
            };
            if (aItems.length > 0) {
                oColumn.template.content.path = aItems[0].getCells()[i].getBinding("text").getPath();
            }
            aTemplate.push(oColumn);
        }
        return aTemplate;
    },
	
	onInit: function() {
		
		var that = this;
//		that.getView().byId('reportTableForNightly').setVisible(true);
//    	that.getView().byId('reportTableForPushV').setVisible(false);
//    	
//		that.getView().byId("branchBox").setVisible(false);
//	   	that.getView().byId("branchLabel").setVisible(false);
//	    var catagoryUrl = python_server+"/trd/catagory";
//		$.ajax({
//			url:catagoryUrl,
//			type:"GET",
//			dataType:"json",			
//		    success : function(data, textStatus, jqXHR){		    		        
//		    	var oModel = new sap.ui.model.json.JSONModel(data);		        
//		        that.getView().byId('catagoryBox').setModel(oModel);		
//		    },
//		    error : function(jqXHR, textStatus, errorThrown) {			    	
//			    sap.m.MessageToast.show("Error");
//			}
//		});

	},
	
	getSplitContObj : function(){
		var result = this.getView().oParent.oParent;
		if(!result){
			jQuery.sap.log.error("SplitApp object can't be found");
		}
		return result;
	},
	
	onShowGraphic: function(){
		var that = this;
		var chartPanel = that.getView().byId("chartPanel");
		
		if (chartPanel.getExpanded()) {			
			
			var version = '';//that.getView().byId("versionBox").getValue();
			var branch = '';//that.getView().byId("branchBox").getValue();
				        
	        postData = {environment:{}};
	        postData.environment.GERRIT_PROJECT = project;
	        if (version!='') {postData.environment.VORA_VERSION = version;}
	        if (catagory == "BDH Nightly Validation") {
	        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";        	
	        } 
	        if (catagory == "BDH Push Validation") {
	        	postData.environment.USE_FOR = "PUSH_VALIDATION";
	        	if(branch!=''){postData.environment.GERRIT_CHANGE_BRANCH = branch;}
	        }
	        var reportUrl = python_server+"/trd/summary/status";

			$.ajax({
				url:reportUrl,
				type:"POST",
				dataType:"json",			
				data: JSON.stringify(postData),
			    success : function(data, textStatus, jqXHR){
			    	var totalCount = 0;
			    	for(var i=0; i<data.dataList.length; i++){
			    		totalCount = totalCount + data.dataList[i].build_summary;			    		 		
			    	}
			    	for(var i=0; i<data.dataList.length; i++){
			    		data.dataList[i].build_rate = parseFloat((data.dataList[i].build_summary/totalCount).toFixed(2));			    					    		 		
			    	}
			    	
			    	//data.dataList[i].duration = (parseInt(end - start)/1000/60/60).toFixed(2);
			    				    			    		        
			        var oVizFrame = that.getView().byId("idVizFrame");			        
			    	oVizFrame.setVisible(true);
			        oVizFrame.setVizProperties({
			            legend: {
			                title: {
			                    visible: true
			                }
			            },
			            title: {
			                visible: true,
			                text: "Build Status Chart"
			            },
			            plotArea: {			            	
	                        dataLabel: {
	                            visible: true
	                        }
	                    }
			        });
			        
			        
			    	var dataModel = new sap.ui.model.json.JSONModel(data);
			        oVizFrame.setModel(dataModel);
			        var oPopOver = that.getView().byId("idPopOver");
			        oPopOver.connect(oVizFrame.getVizUid());			        			        
			        
			    },
			    error : function(jqXHR, textStatus, errorThrown) {			    	
				    sap.m.MessageToast.show("Error");
				}
			});
			
			
			var failReasonUrl = python_server+"/trd/summary/failure";

			$.ajax({
				url:failReasonUrl,
				type:"POST",
				dataType:"json",			
				data: JSON.stringify(postData),
			    success : function(data, textStatus, jqXHR){
			    	
			    				  			        
			        var oVizFrameF = that.getView().byId("idVizFrameFailReason");
			    	oVizFrameF.setVisible(true);
			        oVizFrameF.setVizProperties({
			            legend: {
			                title: {
			                    visible: true
			                }
			            },
			            title: {
			                visible: true,
			                text: "Failure Reason Chart"
			            },
			            plotArea: {
			            	window: {
                                start: "firstDataPoint",
                                end: "lastDataPoint"
                            },
	                        dataLabel: {
	                            visible: true
	                        }
	                    }
			        });
			        
			        
			        var dataModelF = new sap.ui.model.json.JSONModel(data);
			        oVizFrameF.setModel(dataModelF);
			        var oPopOverF = that.getView().byId("idPopOverFailReason");
			        oPopOverF.connect(oVizFrameF.getVizUid());
			    },
			    error : function(jqXHR, textStatus, errorThrown) {			    	
				    sap.m.MessageToast.show("Error");
				}
			});
		} else {
			
		}	
	},
	
	onShowSearchOptions: function(){
		var that = this;			
		
		postData = {environment:{}};
		postData.environment.GERRIT_PROJECT = project;
        if (catagory == "BDH Nightly Validation") {
        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";  
        	
        } 
        if (catagory == "BDH Push Validation") {
        	postData.environment.USE_FOR = "PUSH_VALIDATION";
        	   	
        }
        var reportUrl = python_server+"/trd/search";

		$.ajax({
			url:reportUrl,
			type:"POST",
			dataType:"json",			
			data: JSON.stringify(postData),
		    success : function(data, textStatus, jqXHR){
		    	versionData = {list: [], data:[]};
		    	branchData = {list: [], data: []};
		    	for(var i=0; i<data.dataList.length; i++){
		    		if (data.dataList[i].hasOwnProperty("branch") && branchData.data.indexOf(data.dataList[i].branch) < 0){
		    			branchData.list.push({"branch": data.dataList[i].branch});
		    			branchData.data.push(data.dataList[i].branch);
		    		}
		    		if (data.dataList[i].hasOwnProperty("vora_version")){
		    			if (data.dataList[i].vora_version == "null" || data.dataList[i].vora_version == "NULL"){
		    				var version = "null";		    				 				
		    			} else {
		    				var index = data.dataList[i].vora_version.lastIndexOf("\.");
			    			var version = data.dataList[i].vora_version.substring(0,index);			    			
		    			}
		    			if (versionData.data.indexOf(version) < 0) {
		    				versionData.list.push({"version": version});
		    				versionData.data.push(version);
		    			}	   
		    		}		    		
		    	}
		    	
		    	var versionModel = new sap.ui.model.json.JSONModel();		    	
		    	versionModel.setData(versionData);		    	
			   	that.getView().byId('versionList').setModel(versionModel);
			   	
//			   	var branchModel = new sap.ui.model.json.JSONModel();		    	
//			   	branchModel.setData(branchData);		    	
//			   	that.getView().byId('branchList').setModel(branchModel);			   	
		    },
		    error : function(jqXHR, textStatus, errorThrown) {		    	
			    sap.m.MessageToast.show("Error");
			}
		});
		
	},
	
	onPressSearch: function() {
		var that = this;              
		var catagory = that.getView().byId("catagoryBox").getValue();
		if (catagory==''){
        	sap.m.MessageToast.show("Please choose a catagory!");
        	return;
        }
		var project = that.getView().byId("projectBox").getValue();
		if (project==''){
        	sap.m.MessageToast.show("Please choose a project!");
        	return;
        }
		var version = that.getView().byId("versionBox").getValue();
		var branch = that.getView().byId("branchBox").getValue();
		
        
        postData = {environment:{}};
        postData.environment.GERRIT_PROJECT = project;
        if(version!=''){postData.environment.VORA_VERSION = version;}
        if (catagory == "BDH Nightly Validation") {
        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";
        	var tableController = that.getView().byId('reportTableForNightly');
        	that.getView().byId('reportTableForNightly').setVisible(true);
        	that.getView().byId('reportTableForPushV').setVisible(false);
        } 
        if (catagory == "BDH Push Validation") {
        	postData.environment.USE_FOR = "PUSH_VALIDATION";
        	if(branch!=''){postData.environment.GERRIT_CHANGE_BRANCH = branch;}
        	var tableController = that.getView().byId('reportTableForPushV');
        	that.getView().byId('reportTableForNightly').setVisible(false);
        	that.getView().byId('reportTableForPushV').setVisible(true);
        	
        }
        
		tableController.setBusy(true);
		
		var emptyData = {"results":[]};
        var oEmptyModel = new sap.ui.model.json.JSONModel();
        oEmptyModel.setData(emptyData);
        tableController.setModel(oEmptyModel);
        
        var reportUrl = python_server+"/trd/search";

		$.ajax({
			url:reportUrl,
			type:"POST",
			dataType:"json",			
			data: JSON.stringify(postData),
		    success : function(data, textStatus, jqXHR){
		    	for(var i=0; i<data.dataList.length; i++){
		    		start = new Date(data.dataList[i].start_time);
		    		end = new Date(data.dataList[i].end_time);
		    		if (start != null && end != null && start != 'Invalid Date' && end != 'Invalid Date'){		    			
			    		data.dataList[i].duration = (parseInt(end - start)/1000/60/60).toFixed(2);
		    		} else{
		    			data.dataList[i].duration = "NULL"
		    		}				    		
		    	}
		    	
		    	var oModel = new sap.ui.model.json.JSONModel();		    	
			   	oModel.setData(data);		    	
			   	tableController.setModel(oModel);
			   	
			   	tableController.setBusy(false);
		    },
		    error : function(jqXHR, textStatus, errorThrown) {
		    	tableController.setBusy(false);
			    sap.m.MessageToast.show("Error");
			}
		});
        	
	},
	historyDialog: null,
	onPressHistory: function(evt) {
		var commit_history = evt.oSource.getBindingContext().getObject().commit_history;
		if (commit_history == ""){
			var commit_history_json = {"commit_history": []};
		} else{
			var commit_history_json = JSON.parse(commit_history);
		}
		var oModel = new sap.ui.model.json.JSONModel();
	   	oModel.setData(commit_history_json);
	   	//this.historyDialog.destroy();
		if (!this.historyDialog) {
			this.historyDialog = new sap.m.Dialog({
				title: 'Recent Commits',
				content: new sap.m.Table({
					  id:"commitHistoryTableNightly",			  
					  columns:[
					          new sap.m.Column({
					          header:[
					                  new sap.m.Label({
					                  text:"Date"
					                  })
					                  ]
					          }),new sap.m.Column({
					          header:[
					                  new sap.m.Label({
					                  text:"Author"
					                  })
					                  ]
					          }),new sap.m.Column({
					          header:[
					                  new sap.m.Label({
					                  text:"Commit ID"
					                  })
					                  ]
					          }),new sap.m.Column({
					          header:[
					                  new sap.m.Label({
					                  text:"Message"
					                  })
					                  ]
					          })
					          ],
					  items:{
					        path: '/commit_history',
					        template: new sap.m.ColumnListItem({
					        cells:[
					               new sap.m.Text({
					               text:"{date}"
					               }),
					               new sap.m.Text({
					               text:"{author}"
					               }),
					               new sap.m.Text({
					               text:"{commit}"
					               }),
					               new sap.m.Text({
					               text:"{message}"
					               })
					               ]
					        })
					  	}	
					  }),
				beginButton: new sap.m.Button({
					text: 'Close',
					press: function () {
						this.historyDialog.close();
					}.bind(this)
				})
			});
			this.getView().addDependent(this.historyDialog);			
			//this.historyDialog.bindElement("/");
			//to get access to the global model			
		}
		this.historyDialog.setModel(oModel);
		this.historyDialog.open();
	},
	
	
	/**
	 * Updates the item count within the line item table's header
	 * @param {object} oEvent an event containing the total number of items in the list
	 * @private
	 */
	onUpdateFinished : function (oEvent) {
		var that = this;
		var iTotalItems = oEvent.getParameter("total");
		var oModel =  that.getView().byId('tableTitleNightly').getModel();			    	
		oModel.setProperty("/totalCount", iTotalItems);	
	},
	
	/**
	 * go to the test case detail page
	 */
	toCaseDetail:function(evt){
		var that = this;
		var reportTableController = that.getView().byId('reportTableForNightly');
		reportTableController.setBusy(true);
		if(evt.oSource.getBindingContext().getObject()){
			var build_id = evt.oSource.getBindingContext().getObject().build_id;	
			var build_info = build_id.split(".");		
			
			var postData = {environment:{}};
	        postData.environment.GERRIT_PROJECT = project;	        
	        postData.environment.INFRABOX_BUILD_NUMBER = build_info[0];
	        postData.environment.INFRABOX_BUILD_RESTART_COUNTER = build_info[1];
	        
	        
	        if (catagory == "BDH Nightly Validation") {
	        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";		        	
	        } 
	        if (catagory == "BDH Push Validation") {
	        	postData.environment.USE_FOR = "PUSH_VALIDATION";	        	
	        }
	        	        
			var getCaseList = python_server + "/trd/build/test";
			$.ajax({
				url:getCaseList,
				type:"POST",
				data: JSON.stringify(postData),
				dataType:"json",
	  			success : function(data, textStatus, jqXHR){	
	  				var currentPageView = that.getSplitContObj().getPage("case_detail_nightly");
	  	        	var tableController = currentPageView.byId('caseListNightly'); 
	  	        	var job_data = {dataList:{job_test_runs:[]}};
	  	        	
	  	        	var start = 0;
	  	        	var end = 0;
	  	        	for(var i=0; i<data.jobs.length; i++){
	  	        		if (data.jobs[i].job_state != "failure" ){
	  	        			if(data.jobs[i].job_test_runs.length == 0){
	  	        				end++;
	  	        				job_data.dataList.job_test_runs.push(data.jobs[i]);
		  	        		} else{
		  	        			job_data.dataList.job_test_runs.splice(job_data.dataList.job_test_runs.length-end,0,data.jobs[i]);
		  	        		}	  	        			
	  	        		} else{
	  	        			if(data.jobs[i].job_test_runs.length > 0){
	  	        				start++;
	  	        				job_data.dataList.job_test_runs.unshift(data.jobs[i]);
		  	        		} else{
		  	        			job_data.dataList.job_test_runs.splice(start,0,data.jobs[i]);
		  	        		}
	  	        		}
	  	        		
	  	        	}
					//job_data.dataList.job_test_runs = data.jobs;
					job_data.catagoryId = data.catagory_id;
					
					var oModel = new sap.ui.model.json.JSONModel();
				   	oModel.setData(job_data);
				   	tableController.setModel(oModel);				   
	  				that.getSplitContObj().toDetail("case_detail_nightly", data);	
	  				reportTableController.setBusy(false);	  				
	  			},
	  			error : function(jqXHR, textStatus, errorThrown) {
	  				jQuery.sap.require("sap.m.MessageBox");
	  				sap.m.MessageBox.error("Can't get case list!", {
							title: "Error",
							onClose: null,
							styleClass: "",
							initialFocus: null,
							textDirection: sap.ui.core.TextDirection.Inherit
					});
				}
			});
		}
	},
		
});