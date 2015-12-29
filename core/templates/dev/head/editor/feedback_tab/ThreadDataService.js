// Copyright 2014 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Service for getting thread data from the backend for the
 * feedback tab of the exploration editor.
 *
 * @author sll@google.com (Sean Lip)
 */

oppia.factory('threadDataService', [
    '$http', '$q', 'explorationData', function($http, $q, explorationData) {
  var _expId = explorationData.explorationId;
  var _THREAD_LIST_HANDLER_URL = '/threadlisthandler/' + _expId;
  var _SUGGESTION_LIST_HANDLER_URL = '/suggestionlisthandler/' + _expId;
  var _SUGGESTION_ACTION_HANDLER_URL = '/suggestionactionhandler/' + _expId + '/';
  var _THREAD_HANDLER_PREFIX = '/threadhandler/' + _expId + '/';

  // All the threads for this exploration. This is a list whose entries are
  // objects, each representing threads. The 'messages' key of this object
  // is updated lazily.
  var _data = {
    feedbackThreads: [],
    suggestionThreads: []
  };

  var _fetchThreads = function(successCallback) {
    var fPromise = $http.get(_THREAD_LIST_HANDLER_URL);
    var sPromise = $http.get(_SUGGESTION_LIST_HANDLER_URL, {
      params: {list_type: 'all', has_suggestion: true}
    });

    $q.all([fPromise, sPromise]).then(function(res) {
      _data.feedbackThreads = res[0].data.threads;
      _data.suggestionThreads = res[1].data.threads;
      // Later requests will use only the thread_id, not full_thread_id
      _data.feedbackThreads.concat(_data.suggestionThreads).map(function(val) {
        val.thread_id = val.full_thread_id.substring(
          val.full_thread_id.indexOf(".") + 1, val.full_thread_id.length);
      });
      if (successCallback) {
        successCallback();
      }
    });
  };

  var _fetchMessages = function(threadId) {
    $http.get(_THREAD_HANDLER_PREFIX + threadId).success(function(data) {
      var combined = _data.feedbackThreads.concat(_data.suggestionThreads);
      for (var i = 0; i < combined.length; i++) {
        if (combined[i].thread_id === threadId) {
          combined[i].messages = data.messages;
          combined[i].suggestion = data.suggestion;
          break;
        }
      }
    });
  };

  return {
    data: _data,
    fetchThreads: function(successCallback) {
      _fetchThreads(successCallback);
    },
    fetchMessages: function(threadId) {
      _fetchMessages(threadId);
    },
    createNewThread: function(newSubject, newText, successCallback) {
      $http.post(_THREAD_LIST_HANDLER_URL, {
        state_name: null,
        subject: newSubject,
        text: newText
      }).success(function() {
        _fetchThreads();
        if (successCallback) {
          successCallback();
        }
      });
    },
    addNewMessage: function(threadId, newMessage, newStatus, successCallback, errorCallback) {
      var url = _THREAD_HANDLER_PREFIX + threadId;
      var combined = _data.feedbackThreads.concat(_data.suggestionThreads);
      var thread = null;

      for (var i = 0; i < combined.length; i++) {
        if (combined[i].thread_id === threadId) {
          thread = combined[i];
          thread.status = newStatus;
          break;
        }
      }

      // This is only set if the status has changed.
      var updatedStatus = null;
      if (newStatus !== thread.status) {
        updatedStatus = newStatus;
      }

      var payload = {
        updated_status: newStatus,
        updated_subject: null,
        text: newMessage
      };

      $http.post(url, payload).success(function(data) {
        _fetchMessages(threadId);

        if (successCallback) {
          successCallback();
        }
      }).error(function(data) {
        if (errorCallback) {
          errorCallback();
        }
      });
    },
    resolveSuggestion: function(threadId, action, commitMsg, onSuccess, onFailure) {
      var payload = {
        action: action
      };
      if (commitMsg) {
        payload.commit_message = commitMsg;
      }
      $http.put(_SUGGESTION_ACTION_HANDLER_URL+threadId, payload).success(
        onSuccess).error(onFailure);
    }
  };
}]);
