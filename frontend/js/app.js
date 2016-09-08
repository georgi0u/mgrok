(function() {
  /////////////
  // Helpers //
  /////////////

  var zeroOutTime = function(date) {
    date.setHours(0);
    date.setMinutes(0);
    date.setSeconds(0);
    date.setMilliseconds(0);
    return date;
  };

  var replaceNonAlphaNumChars = function(str) {
    return str.replace(/[.,-\/#!$%\^&\*;:{}=\-_`~()]/g, '');
  }


  /////////////////
  // Controllers //
  /////////////////

  var TheListController = function($scope, $http, $filter) {
    var self = this;
    this.$filter = $filter;
    this.venueNames = [];
    this.eventModel = {};

    $scope['eventModel'] = this.eventModel;

    // Get Venue Data
    $http.get("/data/the_raw_list.json").then(
      function(response) {
        // Add updated date
        self.eventModel['lastUpdated'] = response.data.updated;

        // Add venue data to the scope
        var shows = response.data.shows;
        self.eventModel['venueData'] = shows;

        // Add sorted venue names to the scope
        self.venueNames = [];
        angular.forEach(shows, function(events, venueName) {
          self.venueNames.push(venueName);
        });
        self.venueNames.sort(function (a, b) {
          a = a.toLowerCase().replace(/^the /, '');
          b = b.toLowerCase().replace(/^the /, '');
          return a > b ? 1 : -1;
        });
        self.eventModel['filteredVenues'] = angular.copy(self.venueNames);

        // Add a convenience array of the events to the scope
        self.eventModel['eventList'] = [];
        angular.forEach(
          self.eventModel['venueData'], function(events, venueName) {
            self.eventModel['eventList'] =
              self.eventModel['eventList'].concat(events);
          });

        // Set up a default date filter
        self.eventModel['filterDate'] = function(date) {
          return self.$filter('date')(date, 'EEE, MMM d @ h:mm a');
        };
        
        // Show the next event for each venue
        self.showNextShow();
      },
      function(response) {
        self.eventModel['error'] = 'Something is messed up. Sorry.';
      });
    
    this.eventModel['showDeadVenues'] = true;
  };

  TheListController.prototype.hideAllShows = function() {
    this.eventModel['showing'] = null;
    this.eventModel['eventList'].forEach(function(event) {
      event.show = false;
    });
  };
  
  TheListController.prototype.showNextShow = function() {
    this.hideAllShows();
    this.eventModel['showing'] = 'nextshow';
    var today = new Date();
    angular.forEach(
      this.eventModel['venueData'], function(events, venueName) {
        for (i in events) {
          var event = events[i];
          var eventDate = new Date(event.date);
          if (eventDate >= today) {
            event.show = true;
            break;
          }
        }});
  };

  TheListController.prototype.showNextSevenDays = function() {
    this.hideAllShows();
    this.eventModel['showing'] = 'nextseven';
    var today = new Date();
    var sevenDaysFromNow = new Date();
    sevenDaysFromNow.setDate(today.getDate() + 7);
    this.showBetweenDates(today, sevenDaysFromNow, 'EEE, MMM d @ h:mm a');
  };
  
  TheListController.prototype.alreadyHappened = function(event) {
    var today = zeroOutTime(new Date());
    var eventDate = zeroOutTime(new Date(event.date));
    var eventInThePast = (eventDate.getTime() < today.getTime());
    return eventInThePast;
  };

  TheListController.prototype.isVenueDead = function(venueName) {
    return !this.eventModel['venueData'][venueName].some(function(event) {
      return event.show;
    });
  };

  TheListController.prototype.getEventsToShow = function(venueName) {
    var events = this.eventModel['venueData'][venueName];
    return events.filter(function(event) { return event.show; });
  };

  TheListController.prototype.showBetweenDates =
    function(startDate, endDate, opt_dateFormat) {
      this.eventModel['eventList'].forEach(function(event) {
        var eventDate = new Date(event.date);
        event.show = (
          eventDate.getTime() >= startDate.getTime() &&
            eventDate.getTime() <= endDate.getTime());

      });
      
      var self = this;
      var dateFormat = (opt_dateFormat == undefined) ?
          'EEEE @ h:mm a' : opt_dateFormat;
      this.eventModel['filterDate'] = function(date) {
        return self.$filter('date')(date, dateFormat);
      };
    };

  TheListController.prototype.getEventClass = function(event) {
    var alreadyHappened = this.alreadyHappened(event);
    var contains_link = (event.event_link && event.event_link != '');
    var isToday = this.isToday(event.date)

    return {
      contains_link: contains_link,
      does_not_contain_link: !contains_link,
      past: alreadyHappened,
      today: isToday
    };
  };

  TheListController.prototype.isToday = function(date) {
    date = new Date(date);
    var today = new Date();
    return date.getYear() == today.getYear() &&
      date.getMonth() == today.getMonth() &&
        date.getDate() == today.getDate();
  }

  
  TheListController.prototype.filterVenuesByName = function() {
    var filterStr = this.eventModel['venueFilter'];
    if (!filterStr) {
      this.eventModel['filteredVenues'] = angular.copy(this.venueNames);
      return;
    }
    var filteredVenueNames = [];
    var lowerCaseFilterName = filterStr.toLowerCase();
    this.eventModel['filteredVenues'] = this.venueNames.filter(function(venueName) {
      var lowerCaseVenueName = venueName.toLowerCase();
      var noPunctuationLowerCaseVenueName =
          replaceNonAlphaNumChars(lowerCaseVenueName);
      var noPunctuationFilter =
          replaceNonAlphaNumChars(lowerCaseFilterName);
      return (noPunctuationLowerCaseVenueName.match(noPunctuationFilter) != null)
    });
  };


  ////////////////
  // Directives //
  ////////////////

  var eventTitleTemplate =
    '  <h3 class="datetime"' +
    '      title="{{event.date | date : \'EEE, MMM d @ h:mm a\'}}">'+
    '  <span data-ng-if="theListController.alreadyHappened(event)">already happened on </span>{{eventModel.filterDate(event.date)}}</h3>' +
    '  <div style="position: relative">' +
    '    <ul class="event-artists">' +
    '      <li class="artist" data-ng-repeat="artist in event.artists">{{artist}}</li>' +
    '    </ul>' +
    '    <p class="message" data-ng-transclude></p>' +
    '  </div>';

  var eventTitleDirective = function() {
    return {
      template: eventTitleTemplate,
      transclude: true
    };
  };


  ///////////////////
  // Angular Setup //
  ///////////////////

  angular
    .module('GeorgesListApp', [])
    .controller('TheListController', TheListController)
    .directive('eventTitle', eventTitleDirective);
}());


$(function() {
  // Sticky controls spacer
  var spacer = $('<div>');
  spacer.height($('#controls').outerHeight(true));
  spacer.insertAfter($('footer'));
  
  // Navigation link classes
  $('.selectable li').click(function(event) {
    $(this).siblings().removeClass('selected');
    $(this).addClass('selected');
  });

  // Dead venue button fade/toggle
  $('#dead-venue-filters li').click(function(event) {
    var sibling = $(this).siblings();
    $(this).fadeOut(400, function() {
      sibling.show();
    });
  });

  $("#venueFilter")[0].focus();
});
