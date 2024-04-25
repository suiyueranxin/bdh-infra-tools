<!DOCTYPE HTML>
<html>
	<head>		
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<meta http-equiv='Content-Type' content='text/html;charset=UTF-8'/>
		<Link Rel="SHORTCUT ICON" href="images/Home.ico" />
		<title>BDH Dashboard</title>
		<style type="text/css">  
		        .green {  
		            background-color: #66FF33;   
		        }  
		        .red {  
		            background-color: #FF3300;  
		        }  
		        .yellow {  
		            background-color: #FFFF66; 
		        }
		        .black {
		        	background-color: #071019;
		        }
		        .blue {
		        	background-color: #0000FF;
		        }	
		        .redText {  
		            color: #FF3300 !important;  
		        }  
		        
	    </style>
		<script src="https://sapui5.hana.ondemand.com/sdk/resources/sap-ui-core.js"
				id="sap-ui-bootstrap"
				data-sap-ui-libs="sap.m,sap.ui.commons,sap.ui.table,sap.ui.core"
				data-sap-ui-theme="sap_bluecrystal"
				data-sap-ui-xx-bindingSyntax="complex"
				data-sap-ui-resourceroots='{
					"bdhreport": "bdhreport"
				}'>
				
		</script>
		<!-- only load the mobile lib "sap.m" and the "sap_bluecrystal" theme -->
<%
String username = request.getParameter("username");
if (username == null || username.trim().equals("")) {
    username = request.getRemoteUser();
    if (username == null || username.trim().equals("")) {
        username = "invalid-user";
    }
}
%>
		<script>
				var currentUser = "<%=username%>";
				jQuery.sap.require("sap.ui.core.util.Export");
				jQuery.sap.require("sap.ui.core.util.ExportTypeCSV");
								
				//sap.ui.localResources("bdhreport");
				var app = new sap.m.App({initialPage:"idmain1"});
				var page = sap.ui.view({id:"idmain1", viewName:"bdhreport.main", type:sap.ui.core.mvc.ViewType.XML});
				app.addPage(page);
				app.placeAt("content");
		</script>

	</head>
	<body class="sapUiBody" role="application">
		<div id="content"></div>
	</body>
</html>

